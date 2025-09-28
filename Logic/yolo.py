"""
SORT: A Simple, Online and Realtime Tracker
Copyright (C) 2016-2020 Alex Bewley alex@bewley.ai

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
"""

from __future__ import print_function
import os
import numpy as np
from skimage import io
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import glob
import time
import argparse
from filterpy.kalman import KalmanFilter

np.random.seed(0)

# --- NEW: Multiprocessing-friendly detection output ---
from src.detect_video import detect_video  # your YOLO detection function

vehicle_classes = ["car", "bus", "bike", "person"]

def process_video(video_path):
    """
    Process a video for vehicle detection & tracking.
    Returns a summary dict with counts per vehicle type.
    """
    dets = detect_video(video_path)  # get detections frame-by-frame
    summary = {cls: 0 for cls in vehicle_classes}

    # dets assumed as [[frame, x1, y1, x2, y2, score, class], ...]
    for row in dets:
        cls_name = row[6]  # assuming class is at index 6
        if cls_name in summary:
            summary[cls_name] += 1

    summary["total_vehicles"] = sum(summary.values())
    summary["video"] = os.path.basename(video_path)
    return summary
# --------------------------------------------------------

def linear_assignment(cost_matrix):
    try:
        import lap
        _, x, y = lap.lapjv(cost_matrix, extend_cost=True)
        return np.array([[y[i],i] for i in x if i >= 0])
    except ImportError:
        from scipy.optimize import linear_sum_assignment
        x, y = linear_sum_assignment(cost_matrix)
        return np.array(list(zip(x, y)))

def iou_batch(bb_test, bb_gt):
    bb_gt = np.expand_dims(bb_gt, 0)
    bb_test = np.expand_dims(bb_test, 1)
    xx1 = np.maximum(bb_test[...,0], bb_gt[...,0])
    yy1 = np.maximum(bb_test[...,1], bb_gt[...,1])
    xx2 = np.minimum(bb_test[...,2], bb_gt[...,2])
    yy2 = np.minimum(bb_test[...,3], bb_gt[...,3])
    w = np.maximum(0., xx2 - xx1)
    h = np.maximum(0., yy2 - yy1)
    wh = w*h
    o = wh / ((bb_test[...,2]-bb_test[...,0])*(bb_test[...,3]-bb_test[...,1])
              + (bb_gt[...,2]-bb_gt[...,0])*(bb_gt[...,3]-bb_gt[...,1]) - wh)
    return o

def convert_bbox_to_z(bbox):
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = bbox[0] + w/2.
    y = bbox[1] + h/2.
    s = w*h
    r = w/float(h)
    return np.array([x,y,s,r]).reshape((4,1))

def convert_x_to_bbox(x, score=None):
    w = np.sqrt(x[2]*x[3])
    h = x[2]/w
    if score is None:
        return np.array([x[0]-w/2., x[1]-h/2., x[0]+w/2., x[1]+h/2.]).reshape((1,4))
    else:
        return np.array([x[0]-w/2., x[1]-h/2., x[0]+w/2., x[1]+h/2., score]).reshape((1,5))

class KalmanBoxTracker:
    count = 0
    def __init__(self, bbox):
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.array([[1,0,0,0,1,0,0],[0,1,0,0,0,1,0],[0,0,1,0,0,0,1],[0,0,0,1,0,0,0],
                              [0,0,0,0,1,0,0],[0,0,0,0,0,1,0],[0,0,0,0,0,0,1]])
        self.kf.H = np.array([[1,0,0,0,0,0,0],[0,1,0,0,0,0,0],[0,0,1,0,0,0,0],[0,0,0,1,0,0,0]])
        self.kf.R[2:,2:] *= 10.
        self.kf.P[4:,4:] *= 1000.
        self.kf.P *= 10.
        self.kf.Q[-1,-1] *= 0.01
        self.kf.Q[4:,4:] *= 0.01
        self.kf.x[:4] = convert_bbox_to_z(bbox)
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
    def update(self,bbox):
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(convert_bbox_to_z(bbox))
    def predict(self):
        if (self.kf.x[6]+self.kf.x[2])<=0:
            self.kf.x[6]*=0.0
        self.kf.predict()
        self.age += 1
        if self.time_since_update>0:
            self.hit_streak=0
        self.time_since_update+=1
        self.history.append(convert_x_to_bbox(self.kf.x))
        return self.history[-1]
    def get_state(self):
        return convert_x_to_bbox(self.kf.x)

def associate_detections_to_trackers(dets, trks, iou_threshold=0.3):
    if len(trks)==0:
        return np.empty((0,2),dtype=int), np.arange(len(dets)), np.empty((0,5),dtype=int)
    iou_matrix = iou_batch(dets, trks)
    if min(iou_matrix.shape)>0:
        a = (iou_matrix>iou_threshold).astype(np.int32)
        if a.sum(1).max()==1 and a.sum(0).max()==1:
            matched_indices = np.stack(np.where(a), axis=1)
        else:
            matched_indices = linear_assignment(-iou_matrix)
    else:
        matched_indices = np.empty((0,2))
    unmatched_dets = [d for d in range(len(dets)) if d not in matched_indices[:,0]]
    unmatched_trks = [t for t in range(len(trks)) if t not in matched_indices[:,1]]
    matches=[]
    for m in matched_indices:
        if iou_matrix[m[0],m[1]]<iou_threshold:
            unmatched_dets.append(m[0])
            unmatched_trks.append(m[1])
        else:
            matches.append(m.reshape(1,2))
    if len(matches)==0:
        matches = np.empty((0,2),dtype=int)
    else:
        matches = np.concatenate(matches,axis=0)
    return matches, np.array(unmatched_dets), np.array(unmatched_trks)

class Sort:
    def __init__(self, max_age=1, min_hits=3, iou_threshold=0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.trackers=[]
        self.frame_count=0
    def update(self, dets=np.empty((0,5))):
        self.frame_count+=1
        trks=np.zeros((len(self.trackers),5))
        to_del=[]
        ret=[]
        for t,trk in enumerate(trks):
            pos=self.trackers[t].predict()[0]
            trk[:]=[pos[0],pos[1],pos[2],pos[3],0]
            if np.any(np.isnan(pos)):
                to_del.append(t)
        trks=np.ma.compress_rows(np.ma.masked_invalid(trks))
        for t in reversed(to_del):
            self.trackers.pop(t)
        matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(dets,trks,self.iou_threshold)
        for m in matched:
            self.trackers[m[1]].update(dets[m[0],:])
        for i in unmatched_dets:
            trk=KalmanBoxTracker(dets[i,:])
            self.trackers.append(trk)
        i=len(self.trackers)
        for trk in reversed(self.trackers):
            d=trk.get_state()[0]
            if(trk.time_since_update<1) and (trk.hit_streak>=self.min_hits or self.frame_count<=self.min_hits):
                ret.append(np.concatenate((d,[trk.id+1])).reshape(1,-1))
            i-=1
            if(trk.time_since_update>self.max_age):
                self.trackers.pop(i)
        if len(ret)>0:
            return np.concatenate(ret)
        return np.empty((0,5))
