from __future__ import absolute_import, division
import multiprocessing
import time
import pandas as pd
from psychopy import gui, visual, core, data, logging
from psychopy.constants import (NOT_STARTED, STARTED, FINISHED)
from numpy import (sin, pi, )
import os
from psychopy.hardware import keyboard
import model
import numpy as np


import serial
COM = ""
baud_rate = 9600

#from BlueT import send_code
from lsl_received_data import lsl_received
from djitellopy import  tello

# 自动巡航相关变量
auto_cruise_mode = False  # 自动巡航模式状态
auto_cruise_sequence = [2, 3, 4, 2, 3, 4, 2, 3, 4, 2, 3, 4]  # 1亮灯 2前进两步 3左转 4右转 5后退 6鸣笛 7前进1步
auto_cruise_index = 0  # 当前执行到序列的第几个动作

def decorator(func):
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            return res
        except Exception as e:
            print("执行函数：{}，出现异常：{}".format(func.__name__, e))
    return wrapper

def start_auto_cruise():
    """启动自动巡航模式"""
    global auto_cruise_mode, auto_cruise_index
    auto_cruise_mode = True
    auto_cruise_index = 0
    print("启动自动巡航模式")

def stop_auto_cruise():
    """停止自动巡航模式"""
    global auto_cruise_mode
    auto_cruise_mode = False
    print("停止自动巡航模式")

if __name__ == '__main__':
    multiprocessing.freeze_support()  #防止重复启动

    save_path = "./eeg_data/"
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=lsl_received,args=(queue, save_path))
    process.start()
    trial_dura = 5
    Ename= '脑控小车'
    EInfo = {'参与者姓名': '', '性别': '男','年龄':"22",'小车端口号':'COM'}



    dig= gui.DlgFromDict(dictionary=EInfo, sortKeys=False, title=Ename)
    if dig.OK == False:
        core.quit()
    EInfo['date'] = data.getDateStr()
    EInfo['expName'] = Ename
    filename =  (EInfo['参与者姓名'], Ename,EInfo['性别'],Ename,EInfo['年龄'])

    COM = EInfo['小车端口号']
    ser = serial.Serial(COM, baud_rate)  # 蓝牙

    print(filename)
    endExpNow = False
    frameTolerance = 0.001
    win = visual.Window(
        size=[1920, 1080], fullscr=True, screen=1,
        winType='pyglet', allowGUI=False, allowStencil=False,
        monitor='testMonitor', color=[-1.000, -1.000, -1.000], colorSpace='rgb',
        blendMode='avg', useFBO=True,
        units='height')

    EInfo['frameRate'] = win.getActualFrameRate()
    if EInfo['frameRate'] != None:
        pre_frame_durate = 1.0 / round(EInfo['frameRate'])
        print("frameRate", round(EInfo['frameRate']))
    else:
        pre_frame_durate = 1.0 / 60.0
    defaultKeyboard = keyboard.Keyboard()
    Clock = core.Clock()
    text = visual.TextStim(win=win, name='text'  ,
                           text='脑控小车\n\n按"空格"进行脑机控制\n\n可随时按"ESC"退出',
                           font='Arial',
                           units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                           color='white', colorSpace='rgb', opacity=1,
                           languageStyle='LTR',
                           depth=0.0)
    keys = keyboard.Keyboard()
    # Freq = np.array([8.00, 9.00, 10.00, 11.00, 12.00, 13.00, 14.00, 15.00])
    # Phas = np.array([0, 0.15, 0.3, 0.45, 0.60, 0.75, 0.9, 0])
    Freq = np.array([8.00, 9.00, 10.00, 11.00, 12.00, 13.00])
    Phas = np.array([0, 0.15, 0.3, 0.45, 0.60, 0.75])
    varpy = [600, 90]
    screen_length = 1920
    screen_width = 1080
    x0 = screen_length * 0 / 4 - screen_length / 2
    x1 = screen_length * 1 / 4 - screen_length / 2
    x2 = screen_length * 2 / 4 - screen_length / 2
    x3 = screen_length * 3 / 4 - screen_length / 2
    x4 = screen_length * 4 / 4 - screen_length / 2
    y0 = screen_width * 0 / 4 - screen_width / 2
    y1 = screen_width * 1 / 4 - screen_width / 2
    y2 = screen_width * 2 / 4 - screen_width / 2
    y3 = screen_width * 3 / 4 - screen_width / 2
    y4 = screen_width * 4 / 4 - screen_width / 2

    location = [
        [(x0 + x1) / 2, (y3 + y4) / 2],
        [x2, (y3 + y4) / 2],
        [(x0 + x1) / 2, (y0 + y1) / 2],
        [(x0 + x1) / 2, y2],
        [(x3 + x4) / 2, y2],
        [(x3 + x4) / 2, (y0 + y1) / 2],
        [x2, (y0 + y1) / 2],
        [(x3 + x4) / 2, (y3 + y4) / 2]
    ]
    size_w = 400
    size_h = 400
   # order_lst = ['上升', '前进', '起飞', '左转', '右转', '降落', '后退', '下降']
    order_lst = ['亮灯', '前进', '左转', '右转', '后退', '鸣笛']
    cueClock = core.Clock()
    polygon_0 = visual.Rect(
        win=win, name='polygon_0', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=[1, 1, 1], fillColorSpace='rgb',
        opacity=1, depth=0.0, interpolate=True)
    order_0 = visual.TextStim(win=win, name='text',
                              text='亮灯',
                              font='Arial',
                              units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                              color='white', colorSpace='rgb', opacity=1,
                              languageStyle='LTR',
                              depth=0.0)
    polygon_1 = visual.Rect(
        win=win, name='polygon_1', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=[1, 1, 1], fillColorSpace='rgb',
        opacity=1, depth=-1.0, interpolate=True)
    order_1 = visual.TextStim(win=win, name='text',
                              text='前进',
                              font='Arial',
                              units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                              color='red', colorSpace='rgb', opacity=1,
                              languageStyle='LTR',
                              depth=-1.0)
    # polygon_2 = visual.Rect(
    #     win=win, name='polygon_2', units='pix',
    #     width=[1.0, 1.0][0], height=[1.0, 1.0][1],
    #     ori=0, pos=[0, 0],
    #     lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
    #     fillColor=[1, 1, 1], fillColorSpace='rgb',
    #     opacity=1, depth=-2.0, interpolate=True)
    # order_2 = visual.TextStim(win=win, name='text',
    #                           text='起飞',
    #                           font='Arial',
    #                           units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
    #                           color='red', colorSpace='rgb', opacity=1,
    #                           languageStyle='LTR',
    #                           depth=-2.0)
    polygon_3 = visual.Rect(
        win=win, name='polygon_3', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=[1, 1, 1], fillColorSpace='rgb',
        opacity=1, depth=-3.0, interpolate=True)
    order_3 = visual.TextStim(win=win, name='text',
                              text='左转',
                              font='Arial',
                              units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                              color='red', colorSpace='rgb', opacity=1,
                              languageStyle='LTR',
                              depth=-3.0)

    polygon_4 = visual.Rect(
        win=win, name='polygon_5', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=[1, 1, 1], fillColorSpace='rgb',
        opacity=1, depth=-5.0, interpolate=True)
    order_4 = visual.TextStim(win=win, name='text',
                              text='右转',
                              font='Arial',
                              units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                              color='white', colorSpace='rgb', opacity=1,
                              languageStyle='LTR',
                              depth=-5.0)

    # polygon_5 = visual.Rect(
    #     win=win, name='polygon_6', units='pix',
    #     width=[1.0, 1.0][0], height=[1.0, 1.0][1],
    #     ori=0, pos=[0, 0],
    #     lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
    #     fillColor=[1, 1, 1], fillColorSpace='rgb',
    #     opacity=1, depth=-6.0, interpolate=True)
    # order_5 = visual.TextStim(win=win, name='text',
    #                           text='降落',
    #                           font='Arial',
    #                           units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
    #                           color='white', colorSpace='rgb', opacity=1,
    #                           languageStyle='LTR',
    #                           depth=-6.0)

    polygon_6 = visual.Rect(
        win=win, name='polygon_7', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=[1, 1, 1], fillColorSpace='rgb',
        opacity=1, depth=-7.0, interpolate=True)
    order_6 = visual.TextStim(win=win, name='text',
                              text='后退',
                              font='Arial',
                              units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                              color='white', colorSpace='rgb', opacity=1,
                              languageStyle='LTR',
                              depth=-7.0)

    polygon_7 = visual.Rect(
        win=win, name='polygon_8', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=[1, 1, 1], fillColorSpace='rgb',
        opacity=1, depth=-8.0, interpolate=True)
    order_7 = visual.TextStim(win=win, name='text',
                              text='鸣笛',
                              font='Arial',
                              units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                              color='white', colorSpace='rgb', opacity=1,
                              languageStyle='LTR',
                              depth=-8.0)
    loop_id = -1
    trialClock = core.Clock()
    polygon_trial_0 = visual.Rect(
        win=win, name='polygon_trial_0', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=1.0, fillColorSpace='rgb',
        opacity=1, depth=0.0, interpolate=True)
    order_trial_0 = visual.TextStim(win=win, name='text',
                                    text='亮灯',
                                    font='Arial',
                                    units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                                    color='white', colorSpace='rgb', opacity=1,
                                    languageStyle='LTR',
                                    depth=0.0)

    polygon_trial_1 = visual.Rect(
        win=win, name='polygon_trial_1', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=1.0, fillColorSpace='rgb',
        opacity=1, depth=-1.0, interpolate=True)
    order_trial_1 = visual.TextStim(win=win, name='text',
                                    text='前进',
                                    font='Arial',
                                    units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                                    color='white', colorSpace='rgb', opacity=1,
                                    languageStyle='LTR',
                                    depth=-1.0)
    # polygon_trial_2 = visual.Rect(
    #     win=win, name='polygon_trial_2', units='pix',
    #     width=[1.0, 1.0][0], height=[1.0, 1.0][1],
    #     ori=0, pos=[0, 0],
    #     lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
    #     fillColor=1.0, fillColorSpace='rgb',
    #     opacity=1, depth=-2.0, interpolate=True)
    # order_trial_2 = visual.TextStim(win=win, name='text',
    #                                 text='起飞',
    #                                 font='Arial',
    #                                 units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
    #                                 color='white', colorSpace='rgb', opacity=1,
    #                                 languageStyle='LTR',
    #                                 depth=-2.0)
    polygon_trial_3 = visual.Rect(
        win=win, name='polygon_trial_3', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=1.0, fillColorSpace='rgb',
        opacity=1, depth=-3.0, interpolate=True)
    order_trial_3 = visual.TextStim(win=win, name='text',
                                    text='左转',
                                    font='Arial',
                                    units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                                    color='white', colorSpace='rgb', opacity=1,
                                    languageStyle='LTR',
                                    depth=-3.0)
    polygon_trial_4 = visual.Rect(
        win=win, name='polygon_trial_4', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=[1, 1, 1], fillColorSpace='rgb',
        opacity=1, depth=-5.0, interpolate=True)
    order_trial_4 = visual.TextStim(win=win, name='text',
                                    text='右转',
                                    font='Arial',
                                    units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                                    color='white', colorSpace='rgb', opacity=1,
                                    languageStyle='LTR',
                                    depth=-5.0)

    # polygon_trial_5 = visual.Rect(
    #     win=win, name='polygon_trial_5', units='pix',
    #     width=[1.0, 1.0][0], height=[1.0, 1.0][1],
    #     ori=0, pos=[0, 0],
    #     lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
    #     fillColor=1.0, fillColorSpace='rgb',
    #     opacity=1, depth=-6.0, interpolate=True)
    # order_trial_5 = visual.TextStim(win=win, name='text',
    #                                 text='降落',
    #                                 font='Arial',
    #                                 units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
    #                                 color='white', colorSpace='rgb', opacity=1,
    #                                 languageStyle='LTR',
    #                                 depth=-6.0)
    polygon_trial_6 = visual.Rect(
        win=win, name='polygon_trial_6', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=1.0, fillColorSpace='rgb',
        opacity=1, depth=-7.0, interpolate=True)
    order_trial_6 = visual.TextStim(win=win, name='text',
                                    text='后退',
                                    font='Arial',
                                    units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                                    color='white', colorSpace='rgb', opacity=1,
                                    languageStyle='LTR',
                                    depth=-7.0)
    polygon_trial_7 = visual.Rect(
        win=win, name='polygon_trial_7', units='pix',
        width=[1.0, 1.0][0], height=[1.0, 1.0][1],
        ori=0, pos=[0, 0],
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=1.0, fillColorSpace='rgb',
        opacity=1, depth=-8.0, interpolate=True)
    order_trial_7 = visual.TextStim(win=win, name='text',
                                    text='鸣笛',
                                    font='Arial',
                                    units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                                    color='white', colorSpace='rgb', opacity=1,
                                    languageStyle='LTR',
                                    depth=-8.0)
    globalClock = core.Clock()
    routineTimer = core.CountdownTimer()
    keys.keys = []
    keys.rt = []
    instrComponents = [text, keys]
    for thisComponent in instrComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    Clock.reset(-_timeToFirstFrame)
    frameN = -1
    continueRoutine = True
    # tello = Tello()
    # decorator(tello.connect)()
    # decorator(tello.set_speed)(10)  # 设置 tello 速度
    while continueRoutine:
        t = Clock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=Clock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1
        if text.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            text.frameNStart = frameN
            text.tStart = t
            text.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(text, 'tStartRefresh')
            text.setAutoDraw(True)
        waitOnFlip = False
        if keys.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            keys.frameNStart = frameN
            keys.tStart = t
            keys.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(keys, 'tStartRefresh')
            keys.status = STARTED
            win.callOnFlip(keys.clearEvents, eventType='keyboard')
        if keys.status == STARTED and not waitOnFlip:
            theseKeys = keys.getKeys(keyList=['space'], waitRelease=False)
            if len(theseKeys):
                theseKeys = theseKeys[0]
                if "escape" == theseKeys:
                    endExpNow = True
                continueRoutine = False
        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()
            # decorator(tello.land)()
        if not continueRoutine:
            break
        continueRoutine = False
        for thisComponent in instrComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break
        if continueRoutine:
            win.flip()
    for thisComponent in instrComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    routineTimer.reset()
    trials = data.TrialHandler(nReps=100, method='random',
                               extraInfo=EInfo, originPath=-1,
                               trialList=[None],
                               seed=None, name='trials')
    thisTrial = trials.trialList[0]
    if thisTrial != None:
        for paramName in thisTrial:
            exec('{} = thisTrial[paramName]'.format(paramName))
    result = 0
    for thisTrial in trials:
        restim = visual.TextStim(win, "识别控制指令：" + order_lst[result - 1], font='Arial',
                                 units='pix', pos=(0, 0), height=50, wrapWidth=None, ori=0,
                                 color='red', colorSpace='rgb', opacity=1,
                                 languageStyle='LTR',
                                 depth=0.0)
        currentLoop = trials
        if thisTrial != None:
            for paramName in thisTrial:
                exec('{} = thisTrial[paramName]'.format(paramName))
        routineTimer.add(1.000000)
        polygon_0.setPos((location[0][0], location[0][1]-150))
        order_0.setPos((location[0][0], location[0][1]-150))
        polygon_0.setSize((size_w, size_h))
        polygon_1.setPos((location[1][0], location[1][1]))
        order_1.setPos((location[1][0], location[1][1]))
        polygon_1.setSize((size_w, size_h))
        # polygon_2.setPos((location[2][0],location[2][1]))
        # order_2.setPos((location[2][0], location[2][1]))
        # polygon_2.setSize((size_w, size_h))
        polygon_3.setPos((location[3][0],location[3][1]-250))
        order_3.setPos((location[3][0], location[3][1]-250))
        polygon_3.setSize((size_w, size_h))
        polygon_4.setPos((location[4][0],location[4][1]-250))
        order_4.setPos((location[4][0],location[4][1]-250))
        polygon_4.setSize((size_w, size_h))
        # polygon_5.setPos((location[5][0], location[5][1]))
        # order_5.setPos((location[5][0], location[5][1]))
        # polygon_5.setSize((size_w, size_h))
        polygon_6.setPos((location[6][0], location[6][1]))
        order_6.setPos((location[6][0], location[6][1]))
        polygon_6.setSize((size_w, size_h))
        polygon_7.setPos((location[7][0], location[7][1]-150))
        order_7.setPos((location[7][0], location[7][1]-150))
        polygon_7.setSize((size_w, size_h))
       # selecList = [polygon_0, polygon_1, polygon_2, polygon_3, polygon_4, polygon_5, polygon_6, polygon_7]
        selecList = [polygon_0,polygon_1, polygon_3, polygon_4, polygon_6, polygon_7]
        selecList[loop_id % len(selecList)].setFillColor([1.000, 1.000, 1.000])  # rgb
        loop_id += 1
        selecList[loop_id % len(selecList)].setFillColor([1.000, 1.000, 1.000])  # rgb
        #cueComponents = [polygon_0, polygon_1, polygon_2, polygon_3, polygon_4, polygon_5, polygon_6, polygon_7]
        cueComponents = [polygon_0, polygon_1, polygon_3, polygon_4, polygon_6, polygon_7]
        for thisComponent in cueComponents:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        cueClock.reset(-_timeToFirstFrame)
        frameN = -1
        continueRoutine = True
        while continueRoutine and routineTimer.getTime() > 0:
            t = cueClock.getTime()
            tThisFlip = win.getFutureFlipTime(clock=cueClock)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1
            if polygon_0.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_0.frameNStart = frameN
                polygon_0.tStart = t
                polygon_0.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_0, 'tStartRefresh')
                polygon_0.setAutoDraw(True)
                restim.setAutoDraw(True)
            if polygon_0.status == STARTED:
                if tThisFlipGlobal > polygon_0.tStartRefresh + 1.0 - frameTolerance:
                    polygon_0.tStop = t
                    polygon_0.frameNStop = frameN
                    win.timeOnFlip(polygon_0, 'tStopRefresh')
                    polygon_0.setAutoDraw(False)
            if polygon_1.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_1.frameNStart = frameN
                polygon_1.tStart = t
                polygon_1.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_1, 'tStartRefresh')
                polygon_1.setAutoDraw(True)
            if polygon_1.status == STARTED:
                if tThisFlipGlobal > polygon_1.tStartRefresh + 1.0 - frameTolerance:
                    polygon_1.tStop = t
                    polygon_1.frameNStop = frameN
                    win.timeOnFlip(polygon_1, 'tStopRefresh')
                    polygon_1.setAutoDraw(False)
            # if polygon_2.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            #     polygon_2.frameNStart = frameN
            #     polygon_2.tStart = t
            #     polygon_2.tStartRefresh = tThisFlipGlobal
            #     win.timeOnFlip(polygon_2, 'tStartRefresh')
            #     polygon_2.setAutoDraw(True)
            # if polygon_2.status == STARTED:
            #     if tThisFlipGlobal > polygon_2.tStartRefresh + 1.0 - frameTolerance:
            #         polygon_2.tStop = t
            #         polygon_2.frameNStop = frameN
            #         win.timeOnFlip(polygon_2, 'tStopRefresh')
            #         polygon_2.setAutoDraw(False)
            if polygon_3.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_3.frameNStart = frameN
                polygon_3.tStart = t
                polygon_3.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_3, 'tStartRefresh')
                polygon_3.setAutoDraw(True)
            if polygon_3.status == STARTED:
                if tThisFlipGlobal > polygon_3.tStartRefresh + 1.0 - frameTolerance:
                    polygon_3.tStop = t
                    polygon_3.frameNStop = frameN
                    win.timeOnFlip(polygon_3, 'tStopRefresh')
                    polygon_3.setAutoDraw(False)
            if polygon_4.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_4.frameNStart = frameN
                polygon_4.tStart = t
                polygon_4.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_4, 'tStartRefresh')
                polygon_4.setAutoDraw(True)
            if polygon_4.status == STARTED:
                if tThisFlipGlobal > polygon_4.tStartRefresh + 1.0 - frameTolerance:
                    polygon_4.tStop = t
                    polygon_4.frameNStop = frameN
                    win.timeOnFlip(polygon_4, 'tStopRefresh')
                    polygon_4.setAutoDraw(False)
            # if polygon_5.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            #     polygon_5.frameNStart = frameN
            #     polygon_5.tStart = t
            #     polygon_5.tStartRefresh = tThisFlipGlobal
            #     win.timeOnFlip(polygon_5, 'tStartRefresh')
            #     polygon_5.setAutoDraw(True)
            # if polygon_5.status == STARTED:
            #     if tThisFlipGlobal > polygon_5.tStartRefresh + 1.0 - frameTolerance:
            #         polygon_5.tStop = t
            #         polygon_5.frameNStop = frameN
            #         win.timeOnFlip(polygon_5, 'tStopRefresh')
            #         polygon_5.setAutoDraw(False)
            if polygon_6.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_6.frameNStart = frameN
                polygon_6.tStart = t
                polygon_6.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_6, 'tStartRefresh')
                polygon_6.setAutoDraw(True)
            if polygon_6.status == STARTED:
                if tThisFlipGlobal > polygon_6.tStartRefresh + 1.0 - frameTolerance:
                    polygon_6.tStop = t
                    polygon_6.frameNStop = frameN
                    win.timeOnFlip(polygon_6, 'tStopRefresh')
                    polygon_6.setAutoDraw(False)
            if polygon_7.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_7.frameNStart = frameN
                polygon_7.tStart = t
                polygon_7.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_7, 'tStartRefresh')
                polygon_7.setAutoDraw(True)
            if polygon_7.status == STARTED:
                if tThisFlipGlobal > polygon_7.tStartRefresh + 1.0 - frameTolerance:
                    polygon_7.tStop = t
                    polygon_7.frameNStop = frameN
                    win.timeOnFlip(polygon_7, 'tStopRefresh')
                    polygon_7.setAutoDraw(False)
            if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
                core.quit()
            if not continueRoutine:
                break
            continueRoutine = False
            for thisComponent in cueComponents:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break
            if continueRoutine:
                win.flip()
        for thisComponent in cueComponents:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        polygon_trial_0.setPos((location[0][0], location[0][1]-150))
        order_trial_0.setPos((location[0][0], location[0][1]-150))
        polygon_trial_0.setSize((size_w, size_h))
        polygon_trial_1.setPos((location[1][0], location[1][1]))
        order_trial_1.setPos((location[1][0], location[1][1]))
        polygon_trial_1.setSize((size_w, size_h))
        # polygon_trial_2.setPos((location[2][0], location[2][1]))
        # order_trial_2.setPos((location[2][0], location[2][1]))
        # polygon_trial_2.setSize((size_w, size_h))
        polygon_trial_3.setPos((location[3][0], location[3][1]-250))
        order_trial_3.setPos((location[3][0], location[3][1]-250))
        polygon_trial_3.setSize((size_w, size_h))
        polygon_trial_4.setPos((location[4][0], location[4][1]-250))
        order_trial_4.setPos((location[4][0], location[4][1]-250))
        polygon_trial_4.setSize((size_w, size_h))
        # polygon_trial_5.setPos((location[5][0],location[5][1]))
        # order_trial_5.setPos((location[5][0], location[5][1]))
        # polygon_trial_5.setSize((size_w, size_h))
        polygon_trial_6.setPos((location[6][0], location[6][1]))
        order_trial_6.setPos((location[6][0], location[6][1]))
        polygon_trial_6.setSize((size_w, size_h))
        polygon_trial_7.setPos((location[7][0], location[7][1]-150))
        order_trial_7.setPos((location[7][0], location[7][1]-150))
        polygon_trial_7.setSize((size_w, size_h))
        # seleclist2 = [polygon_trial_0, polygon_trial_1, polygon_trial_2, polygon_trial_3, polygon_trial_4,
        #               polygon_trial_5,
        #               polygon_trial_6, polygon_trial_7]

        seleclist2 = [polygon_trial_0, polygon_trial_1, polygon_trial_3, polygon_trial_4,
                      polygon_trial_6, polygon_trial_7]

        # trialComponents = [polygon_trial_0, polygon_trial_1, polygon_trial_2, polygon_trial_3, polygon_trial_4,
        #                    polygon_trial_5, polygon_trial_6, polygon_trial_7]
        trialComponents = [polygon_trial_0, polygon_trial_1, polygon_trial_3, polygon_trial_4
                        , polygon_trial_6, polygon_trial_7]
        for thisComponent in trialComponents:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        trialClock.reset(-_timeToFirstFrame)
        frameN = -1
        continueRoutine = True

        queue.put("start-1")
        begin_time = time.time()
        while continueRoutine:
            t = trialClock.getTime()
            tThisFlip = win.getFutureFlipTime(clock=trialClock)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1
            restim.setAutoDraw(False)
            if polygon_trial_0.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_trial_0.frameNStart = frameN
                polygon_trial_0.tStart = t
                polygon_trial_0.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_trial_0, 'tStartRefresh')
                polygon_trial_0.setAutoDraw(True)
                order_trial_0.setAutoDraw(True)
            if polygon_trial_0.status == STARTED:
                if tThisFlipGlobal > polygon_trial_0.tStartRefresh + trial_dura - frameTolerance:
                    polygon_trial_0.tStop = t
                    polygon_trial_0.frameNStop = frameN
                    win.timeOnFlip(polygon_trial_0, 'tStopRefresh')
                    polygon_trial_0.setAutoDraw(False)
                    order_trial_0.setAutoDraw(False)
            if polygon_trial_0.status == STARTED:
                polygon_trial_0.setFillColor([1, 1, 1], log=False)
            if polygon_trial_1.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_trial_1.frameNStart = frameN
                polygon_trial_1.tStart = t
                polygon_trial_1.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_trial_1, 'tStartRefresh')
                polygon_trial_1.setAutoDraw(True)
                order_trial_1.setAutoDraw(True)
            if polygon_trial_1.status == STARTED:
                if tThisFlipGlobal > polygon_trial_1.tStartRefresh + trial_dura - frameTolerance:
                    polygon_trial_1.tStop = t
                    polygon_trial_1.frameNStop = frameN
                    win.timeOnFlip(polygon_trial_1, 'tStopRefresh')
                    polygon_trial_1.setAutoDraw(False)
                    order_trial_1.setAutoDraw(False)
            if polygon_trial_1.status == STARTED:
                polygon_trial_1.setFillColor([1, 1, 1], log=False)
            # if polygon_trial_2.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            #     polygon_trial_2.frameNStart = frameN
            #     polygon_trial_2.tStart = t
            #     polygon_trial_2.tStartRefresh = tThisFlipGlobal
            #     win.timeOnFlip(polygon_trial_2, 'tStartRefresh')
            #     polygon_trial_2.setAutoDraw(True)
            #     order_trial_2.setAutoDraw(True)
            # if polygon_trial_2.status == STARTED:
            #     if tThisFlipGlobal > polygon_trial_2.tStartRefresh + trial_dura - frameTolerance:
            #         polygon_trial_2.tStop = t
            #         polygon_trial_2.frameNStop = frameN
            #         win.timeOnFlip(polygon_trial_2, 'tStopRefresh')
            #         polygon_trial_2.setAutoDraw(False)
            #         order_trial_2.setAutoDraw(False)
            # if polygon_trial_2.status == STARTED:
            #     polygon_trial_2.setFillColor([1, 1, 1], log=False)
            if polygon_trial_3.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_trial_3.frameNStart = frameN
                polygon_trial_3.tStart = t
                polygon_trial_3.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_trial_3, 'tStartRefresh')
                polygon_trial_3.setAutoDraw(True)
                order_trial_3.setAutoDraw(True)
            if polygon_trial_3.status == STARTED:
                if tThisFlipGlobal > polygon_trial_3.tStartRefresh + trial_dura - frameTolerance:
                    polygon_trial_3.tStop = t
                    polygon_trial_3.frameNStop = frameN
                    win.timeOnFlip(polygon_trial_3, 'tStopRefresh')
                    polygon_trial_3.setAutoDraw(False)
                    order_trial_3.setAutoDraw(False)
            if polygon_trial_3.status == STARTED:
                polygon_trial_3.setFillColor([1, 1, 1], log=False)
            if polygon_trial_4.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_trial_4.frameNStart = frameN
                polygon_trial_4.tStart = t
                polygon_trial_4.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_trial_4, 'tStartRefresh')
                polygon_trial_4.setAutoDraw(True)
                order_trial_4.setAutoDraw(True)
            if polygon_trial_4.status == STARTED:
                if tThisFlipGlobal > polygon_trial_4.tStartRefresh + trial_dura - frameTolerance:
                    polygon_trial_4.tStop = t
                    polygon_trial_4.frameNStop = frameN
                    win.timeOnFlip(polygon_trial_4, 'tStopRefresh')
                    polygon_trial_4.setAutoDraw(False)
                    order_trial_4.setAutoDraw(False)
            if polygon_trial_4.status == STARTED:
                polygon_trial_4.setFillColor([1, 1, 1], log=False)
            # if polygon_trial_5.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            #     polygon_trial_5.frameNStart = frameN
            #     polygon_trial_5.tStart = t
            #     polygon_trial_5.tStartRefresh = tThisFlipGlobal
            #     win.timeOnFlip(polygon_trial_5, 'tStartRefresh')
            #     polygon_trial_5.setAutoDraw(True)
            #     order_trial_5.setAutoDraw(True)
            # if polygon_trial_5.status == STARTED:
            #     if tThisFlipGlobal > polygon_trial_5.tStartRefresh + trial_dura - frameTolerance:
            #         polygon_trial_5.tStop = t
            #         polygon_trial_5.frameNStop = frameN
            #         win.timeOnFlip(polygon_trial_5, 'tStopRefresh')
            #         polygon_trial_5.setAutoDraw(False)
            #         order_trial_5.setAutoDraw(False)
            # if polygon_trial_5.status == STARTED:
            #     polygon_trial_5.setFillColor([1, 1, 1], log=False)
            if polygon_trial_6.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_trial_6.frameNStart = frameN
                polygon_trial_6.tStart = t
                polygon_trial_6.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_trial_6, 'tStartRefresh')
                polygon_trial_6.setAutoDraw(True)
                order_trial_6.setAutoDraw(True)
            if polygon_trial_6.status == STARTED:
                if tThisFlipGlobal > polygon_trial_6.tStartRefresh + trial_dura - frameTolerance:
                    polygon_trial_6.tStop = t
                    polygon_trial_6.frameNStop = frameN
                    win.timeOnFlip(polygon_trial_6, 'tStopRefresh')
                    polygon_trial_6.setAutoDraw(False)
                    order_trial_6.setAutoDraw(False)
            if polygon_trial_6.status == STARTED:
                polygon_trial_6.setFillColor([1, 1, 1], log=False)
            if polygon_trial_7.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                polygon_trial_7.frameNStart = frameN
                polygon_trial_7.tStart = t
                polygon_trial_7.tStartRefresh = tThisFlipGlobal
                win.timeOnFlip(polygon_trial_7, 'tStartRefresh')
                polygon_trial_7.setAutoDraw(True)
                order_trial_7.setAutoDraw(True)
            if polygon_trial_7.status == STARTED:
                if tThisFlipGlobal > polygon_trial_7.tStartRefresh + trial_dura - frameTolerance:
                    polygon_trial_7.tStop = t
                    polygon_trial_7.frameNStop = frameN
                    win.timeOnFlip(polygon_trial_7, 'tStopRefresh')
                    polygon_trial_7.setAutoDraw(False)
                    order_trial_7.setAutoDraw(False)
            if polygon_trial_7.status == STARTED:
                polygon_trial_7.setFillColor([1, 1, 1], log=False)
            Amp = (sin(2 * pi * Freq * frameN / 60 + Phas) - 0.5) * 2.0
            for idx in range(6):
                seleclist2[idx].setFillColor([Amp[idx]])
            if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
                core.quit()
            if not continueRoutine:
                break
            continueRoutine = False
            for thisComponent in trialComponents:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break
            if continueRoutine:
                win.flip()
        queue.put("ending")
        time.sleep(1)
        np_array = pd.read_csv(os.path.join(save_path, "temp.csv")).to_numpy()
        data_len = np_array.shape[0]
        np_array = np_array[data_len - 4 * 500: data_len,0:8]
        np_array = np_array.transpose(1, 0)
        np_array = model.resample_eeg_data(np_array, 250 * 4)


        print("识别数据形状:{}".format(np_array.shape))
        # fbcca= model.FBCCA(Num_haimonics =5, fs=250, sample_len =1000, Num_fb=4, n_components=1)
        
        # 定义动作列表
        order_lst = ['亮灯', '前进', '左转', '右转', '后退', '鸣笛']
        #             1        2        3        4        5        6        7为前进1步
        
        result = model.fbcca_classify(np_array)
        print("result:", result, order_lst[result - 1])

        # 检查是否为自动巡航模式
        if auto_cruise_mode:
            # 自动巡航模式下，直接修改result为序列中的下一个动作
            if auto_cruise_index < len(auto_cruise_sequence):
                result = int(auto_cruise_sequence[auto_cruise_index])
                print(f"自动巡航执行动作: {result} - {order_lst[result - 1]}")
                auto_cruise_index += 1
                if auto_cruise_index >= len(auto_cruise_sequence):
                    # 序列执行完毕，停止自动巡航
                    stop_auto_cruise()
                    print("自动巡航序列执行完毕")
        elif result == 5:
            # 检测到"后退"，启动自动巡航
            start_auto_cruise()
            print("启动自动巡航模式")
            # 直接修改result为第一个自动巡航动作
            if auto_cruise_index < len(auto_cruise_sequence):
                result = int(auto_cruise_sequence[auto_cruise_index])
                print(f"自动巡航执行动作: {result} - {order_lst[result - 1]}")
                auto_cruise_index += 1

        # result += 1
        # order_lst = ['上升', '前进', '起飞', '左转', '右转', '降落', '后退', '下降']
        #代码默认为COM3可以根据实际改
        if result==1:
            ser.write(b'5')
        elif result==2:
            ser.write(b'2')
            time.sleep(0.3)
            ser.write(b'2')
        elif result==3:
            ser.write(b'3')
        elif result==4:
            ser.write(b'4')
        elif result==5:
            ser.write(b'1')
        elif result==6:
            ser.write(b'6')
        elif result==7:
            ser.write(b'2')
        # if result == 1:
        #     decorator(tello.move_up)(50)
        # elif result == 2:
        #     decorator(tello.move_forward)(50)
        # elif result == 3:
        #     decorator(tello.takeoff)()
        # elif result == 4:
        #     decorator(tello.move_left)(50)
        # elif result == 5:
        #     decorator(tello.move_right)(50)
        # elif result == 6:
        #     decorator(tello.land)()
        # elif result == 7:
        #     decorator(tello.move_back)(50)
        # elif result == 8:
        #     decorator(tello.move_down)(50)
        for thisComponent in trialComponents:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        routineTimer.reset()
    win.flip()
    logging.flush()
    win.close()
    core.quit()
    # decorator(tello.land)()
