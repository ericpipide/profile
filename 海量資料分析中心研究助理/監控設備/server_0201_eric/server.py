import platform,os,time
import psutil as ps

#網路
net_counter = ps.net_io_counters(pernic=True)
for i in net_counter:
    print(net_counter[i])
    if net_counter[i].bytes_sent >= 1:
        s1 = ps.net_io_counters(pernic=True)[i]
        time.sleep(2)
        s2 = ps.net_io_counters(pernic=True)[i]
        result = s2.bytes_recv - s1.bytes_recv
        reslut = float(result/1024)
        print(str('%d' % (result)) + 'kb/s')
    #print("網路卡："+i+" ,網路卡資訊：",net_counter[i])                

#進程
for i in ps.pids():
    p = ps.Process(i)
    try:
        if p.name() == 'python.exe':
            print(p.status())
            print(p.cpu_times())
            print(p.memory_info())
            print(p.num_threads())
            print(p.threads())
    except:
        pass