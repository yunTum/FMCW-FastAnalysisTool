# coding: UTF-8
from faulthandler import disable
from turtle import update
import numpy as np
import matplotlib.pyplot as plt

import datetime
import PySimpleGUI as sg
import functions as fc
import time
import threading

#################################################

def del_plot(fig):
    plt.close()


sg.theme('DarkGrey9')

layout = [
    [sg.Text('ADC File', size=(15, 1), justification='right'),sg.InputText('', enable_events=True,),sg.FilesBrowse('Select file', key='-FILES-', file_types=(("ADC ファイル", "*"),))],
    [sg.Text('Analysis Method')],
    [sg.Radio('PM Time/2', 'radio_how',default=True, key='tim'),sg.Radio('Average', 'radio_how',key='ave'), sg.Radio('Binarization', 'radio_how', key='bin'), sg.Text('Phase Modulation', pad=((80,0),0)),sg.InputText(size=(6,2),key='-InputFreq-', default_text='500'), sg.Text('kHz')],
    [sg.Text('Threshold [mV]'),sg.Slider(range=(0,5),default_value =1,resolution=0.1,orientation='h',size=(34.3, 20),enable_events=True,key='slider_vth')],
    [sg.Text('ADC Sampling'), sg.InputText(size=(6,2),key='-InputSamp-', default_text='500'), sg.Text('[MHz]'),sg.Text('FFT range [Hz]',pad=((100,0),0)), sg.Text('Max'), sg.InputText(size=(6,2),key='-fftMax-', default_text='3000'), sg.Text('dHz'),sg.InputText(size=(4,2),key='-fftdHz-', default_text='500')],
    [sg.Checkbox("File Save", default=False,pad=((200,20),0), key='sv_flg'), sg.Button('RUN',key='-run-', size=(8, 2),pad=((0,10),0), disabled=True), sg.Button('EVENT',key='-event-', size=(8, 2),pad=((0,10),0),disabled=True), sg.Button('FFT',key='-fft-', size=(8, 2),pad=((0,10),0),disabled=True), sg.Button('CLEAR',key='-clear-', size=(8, 2), disabled=True)],
    [sg.Multiline('', disabled=True, key='-log', size=(80, 6))]
        ]

window = sg.Window('Plot', layout, location=(100, 100), finalize=True)
file_path = ""
methodFlg = 0
methodName = ""
while True:
    event, values = window.read()

    if event in (None, 'Exit'):
        break

    elif event == '-run-':
        if values['tim']:
            methodFlg = 0
            methodName = 'tim'
        elif values['ave']:
            methodFlg = 1
            methodName = 'ave'
        elif values['bin']:
            methodFlg = 2
            methodName = 'bin'

        eventData, dataFrame = fc.analysisData(window, file_path, values['-InputFreq-'], methodFlg,  values['slider_vth'])
        date = datetime.datetime.now()
        window['-log'].print(date)
        window['-fft-'].update(disabled=False)
        window['-event-'].update(disabled=False)
        #fig_ = make_data_fig(make=True)
        #draw_plot(fig_)

    elif event == '-event-':
        threadEventPlt = threading.Thread(target=
            fc.eventPlt(window, eventData, dataFrame, methodFlg, date, methodName, file_path, values['sv_flg'])
        )
        threadEventPlt.start()

    elif event == '-fft-':
        threadFFTPlt = threading.Thread(target=
            fc.fftPlt(window, eventData, date, methodName, file_path, values['sv_flg'], int(values['-fftMax-']), int(values['-fftdHz-']), int(values['-InputSamp-'])*10**6, int(values['-InputFreq-']))
        )
        threadFFTPlt.start()

    elif event == '-clear-':
        del_plot()

    elif values['-FILES-'] != '':
        #print('FilesBrowse')
        #print(values['-FILES-'].split(';'))
        file_path = values['-FILES-'].split(';')[0]
        window['-run-'].update(disabled=False)

window.close()