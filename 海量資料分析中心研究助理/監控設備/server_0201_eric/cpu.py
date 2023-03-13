import platform,os,wmi
from numpy import logical_and
import psutil as ps

print(platform.processor()) #cpu名稱
print(os.cpu_count()) #系統cpu數量
print(ps.cpu_percent()) 
print(ps.cpu_stats())
print(ps.cpu_freq())
print(ps.cpu_times())

print('\n')
#ram的數據
print(ps.virtual_memory())
print(ps.swap_memory())