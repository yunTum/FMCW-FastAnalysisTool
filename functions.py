# coding: UTF-8
import os
import sys
import pandas as pd
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt

#analysis functions
def to_little(val):
#little endian
#EXAMPLE
#16: FF07
#2 : 11111111 00000111
#           |
#    Little Endian
#2 : 00000111 11111111
#    0000           ->  4bit non
#    0111 1111 1111 -> 12bit adc data
#16: 07FF
#10: 2045

  little_hex = bytearray.fromhex(val)
  little_hex.reverse()
  str_little = ''.join(format(x, '02x') for x in little_hex)

  return str_little

def to_volt(dec):
    dec_to_mV = 0.244140625     #mV/dec
    n = -500                    #mV

    if dec <= 2047:
        volt = n + dec_to_mV * dec
    else :
        volt = dec_to_mV * (dec - 2048)

    return volt

def freq_occurence(data, threshold):
    #threshold [mV]
    return sum(1 for x in data if x[2] >= threshold)

def photon_count(data, items):
    #resolution [mV]
    resolve_volt = 0.244140625

    return sum(x[2]/resolve_volt for x in data)/items


def event_bool(data, threshold):
    if data[2] >= threshold:
        return 1
    else:
        return 0

def create_dataframe(data, freqMod, flg, vth):
    dec_list = []
    idx = 0
    time = 0
    data_length = int(len(data)/2)

    for i in range(data_length):
        HEXlist = []
        dec_list_row = []

        for j in range(2):

                HEXlist.append("{0:02x}".format(data[idx]))
                idx += 1

        result = ''.join(HEXlist)
        little_endian = to_little(result)
        #print("Hex to int:", int(little_endian, 16))
        dec_list_row.append(time)
        dec_list_row.append(int(little_endian, 16))
        volt = to_volt(int(little_endian, 16))
        if volt > 0:
            dec_list_row.append(to_volt(int(little_endian, 16)))
        else:
            dec_list_row.append(0)
        dec_list.append(dec_list_row)

        time += 2


    an_Time = 2                     #T/(an_Time <- here)
    if flg==0:
        #Event calc########################
        freq = freqMod*10**3                         #Hz

        time_idx = ((1/freq)/ an_Time ) *10**9         # T/an_Time [ns]

        cotime_idx = int(time_idx / 2)          #1item per 2ns
        last_idx = len(dec_list) - cotime_idx

        for i in range(last_idx):
            dec_list[i].append(freq_occurence(dec_list[i:i+cotime_idx-1], vth))
        ###################################

    elif flg==1:
        #Event calc########################
        time_idx = 500 #移動平均[個]

        last_idx = len(dec_list) - time_idx

        for i in range(last_idx):
            dec_list[i].append(photon_count(dec_list[i:i+time_idx-1], time_idx))
        ###################################

    else:
        for i in range(len(dec_list)):
            dec_list[i].append(event_bool(dec_list[i], vth))

    return dec_list
    #return dec_list[int(data_length/2):data_length]

def fftFunc(data,fs_in):
    N =len(data)                    #データ長
    fs=fs_in                    #サンプリング周波数 500000000
    dt =1/fs                        # サンプリング間隔
    t = np.arange(0.0, N*dt, dt)    #時間軸
    freq = np.linspace(0, fs,N)     #周波数軸
    fn=1/dt/2                       #ナイキスト周波数
    F=np.fft.fft(data)/(N/2)
    #F=np.fft.fft(X,norm="ortho")
    F[(freq>fn)]=0                  #ナイキスト周波数以降をカット
    F[0] = 0
    #print(np.abs(F))
    F_abs = np.abs(F)
    F_edited = (F_abs - F_abs.min()) / (F_abs.max() - F_abs.min())

    return  F_edited, freq

def array2df(arg1, arg2):
    length = len(arg1)
    df_data = []
    for i in range(length):
        df_data.append([arg1[i], arg2[i]])
    return df_data

def rePath(path):
    print(os.path.dirname(path))
    rPath = os.path.dirname(path)
    return rPath

def analysisData(window, path, freqMod, methodFlg, vth):
    vth = float(vth)
    freqMod = int(freqMod)
    #Proc Start##################

    t_start = time.process_time()

    f = open(path,"rb")
    tmp = f.read()
    f.close()
    data = create_dataframe(tmp, freqMod, methodFlg, vth)

    df = pd.DataFrame(data, columns=['Time', 'ADC', 'Voltage', 'Event'])
    eventData = df['Event'].tolist()
    t_end = time.process_time()
    window['-log'].print("Processing time:", t_end-t_start)
    #Proc End#####################

    window['-log'].print("Done")
    return eventData, df

def fftPlt(window, eventData, date, methodName, path, save_flg, maxrangeHz, dHz, fs, Fmod):

    now_str = date.strftime("%Y%m%d%H%M%S")

    fft_data = [x for x in eventData if np.isnan(x) == False]
    F_edited, freq = fftFunc(fft_data, fs)
    main_lobe = sorted(F_edited.ravel())[-1]
    side_lobe = sorted(F_edited.ravel())[-2]
    window['-log'].print("Side lobe:", '{:.5f}'.format(side_lobe))

    #Plot#########
    # range_Hz = 3000
    # dHz = 500

    df_fft_data = array2df(freq/1000, F_edited) #kHz
    df_fft = pd.DataFrame(df_fft_data, columns=['Freqency', 'AMP'])

    plt.plot(freq/1000,F_edited)#
    plt.xlabel("[kHz]")
    plt.ylabel("Amp")
    plt.yticks(np.arange(0.0, 1.0 + 0.1, 0.1))
    plt.xticks(np.arange(0, maxrangeHz + 1, dHz))
    plt.xlim(-0.01,maxrangeHz)
    plt.grid()    

    #Save data#####
    if save_flg:
        fileDict = os.path.dirname(path)
        fileName = os.path.basename(path)
        folder_path = fileDict + '/' + now_str + '+' + methodName + '_' + fileName + "_analysis-folder"
        if not os.path.exists(folder_path): #ディレクトリ存在確認
            os.mkdir(folder_path)
        df_fft.to_csv(folder_path + '/FFT.csv', index=False)
        plt.savefig(folder_path + '/FFT_data.png', format="png", dpi=300)
        with open(folder_path + '/analysis_data.txt',"w") as f:
            f.write('Modulated Freq. : ' + str(Fmod) + 'kHz\n')
            f.write('FFT Sampling Freq. : ' + str(500) + 'MHz\n')
            f.write('Main lobe : ' + str(main_lobe) + '\n')
            #f.write('Main lobe Freq. : ' + str(main_freq) + '\n')
            f.write('Side lobe : ' + str(side_lobe) + '\n')
            #f.write('Side lobe Freq. : ' + str(side_freq) + '\n')
            window['-log'].print("FFT Save")
    window['-log'].print("FFT Done")
    plt.show(block=False)

def eventPlt(window, eventData, dataFrame, methodFlg, date, methodName, path, save_flg):
    now_str = date.strftime("%Y%m%d%H%M%S")
    #Plot#########
    t = np.arange(0.0, len(eventData), 1)
    # fig = plt.figure()
    # ax = fig.add_subplot(111)

    if methodFlg == 0  or methodFlg == 1 or methodFlg == 2:
        plt.plot(t, eventData)
    else:
        plt.scatter(t, eventData, s=1)
    plt.xlabel("[Time]")
    plt.ylabel("Event")
    plt.grid()
    
    #Save data#####
    if save_flg:
        fileDict = os.path.dirname(path)
        fileName = os.path.basename(path)
        folder_path = fileDict + '/' + now_str + '+' + methodName + '_' + fileName + "_analysis-folder"
        if not os.path.exists(folder_path): #ディレクトリ存在確認
            os.mkdir(folder_path)
        plt.savefig(folder_path + '/event_data.png', format="png", dpi=300)
        dataFrame.to_csv(folder_path + '/ADC_data.csv', index=False)
        window['-log'].print("Event Save")
    window['-log'].print("Event Done")
    plt.show(block=False)
    #plt.close()
