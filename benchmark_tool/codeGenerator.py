
##### 调用相关库

import argparse
import subprocess
import os
import re
import json
from jinja2 import Template
from jinja2 import Environment, FileSystemLoader
import serial
import serial.tools.list_ports
import time
import shutil
import pandas as pd
import matplotlib.pyplot as plt


## 定义绘图函数
def read_and_process_file(file_path):
    data = {}
    current_frequency = None

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith("Evaluation-"):
                current_frequency = int(line.split('-')[1].split()[0])
                data[current_frequency] = {}
            elif ":" in line and current_frequency is not None:
                key, value = line.split(":")
                key = key.strip()
                try:
                    value = int(value.strip())
                except ValueError:
                    continue  # 忽略无法转换为整数的行
                data[current_frequency][key] = value

    return pd.DataFrame.from_dict(data, orient='index').fillna(0)


def plot_histogram_as_lines(df):
    plt.figure(figsize=(12, 8))

    for index, row in df.iterrows():
        plt.plot(row.index, row.values, marker='o', label=f"Frequency {index}")
    plt.title("Histograms as Line Plots for Frequencies")
    plt.xlabel("Execution Time")
    plt.ylabel("Count")
    plt.legend(title="Frequencies")
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', linewidth=0.7)
    plt.tight_layout()
    plt.show()

#### 主程序
#### Part1 获取输入
print("code generator starts");

## 获得参数列表
parser=argparse.ArgumentParser(description='code generator input')
parser.add_argument('--os','-o',type=int,default=0,required=True)     #  0 = Nuttx  1 = FreeRTOS  2=FMP
parser.add_argument('--core','-c',type=int,default=4,required=False)
parser.add_argument('--step','-s',type=int,default=10,required=False)
parser.add_argument('--loop','-l',type=int,default=10,required=False)
parser.add_argument('--type','-t',type=int,default=0,required=False)   #  0 = workload  1 = scalability
parser.add_argument('--pattern','-p',type=int,default=1,required=True)
parser.add_argument('--subpattern','-sp',type=int,default=None,required=False)

args=parser.parse_args()

## 测试输入
print("RTOS:"+str(args.os))
print("active core: "+str(args.core))
print("workload step: "+str(args.step))
print("execution loop length: "+str(args.loop))
print("scenario_type: "+str(args.type))
print("pattern: "+str(args.pattern))
if args.subpattern!=None:
   print("pattern: "+str(args.subpattern))


#### Part2 生成代码

## 根据输入获得user配置
user_config={
    "active_core": args.core,
    "execution_loop": args.loop,
    "execution_step":args.step, }  

## 根据os选择加载json
if args.os==0:
   json_path = "source/RTOS/Nuttx/System/system.json"
elif args.os==1:
   json_path = "source/RTOS/FreeRTOS/System/system.json"
elif args.os==2: 
   json_path = "source/RTOS/FMP/System/system.json"
else:
   print("os select error")
with open(json_path, 'r') as f:
   RTOS_json = json.load(f)

## 通过获得RTOS_template路径并填入user_config
RTOS_template_path = RTOS_json["RTOS_templates"]
user_config["selected_sub_template"] = RTOS_template_path

## 加载jinja2环境
env=Environment(loader=FileSystemLoader(os.getcwd()),lstrip_blocks=False)

## 获取模版路径
scenario_type = "Workload" if args.type==0 else "Scalability"
if args.type == 0:
   if args.pattern == 4 and args.subpattern:
      template_path = f"source/Benchmark/{scenario_type}/Pattern{args.pattern}-{args.subpattern}_template.jinja"
   else:
      template_path = f"source/Benchmark/{scenario_type}/Pattern{args.pattern}_template.jinja"
elif args.type == 1:
   if args.pattern in [1,2,4,5,6]:
      template_path = f"source/Benchmark/{scenario_type}/Pattern{args.pattern}_template.jinja"
else:
   print("error scnario type")

## 获取主模版
template = env.get_template(template_path)
## 渲染模版
generated_code =template.render(user_config)

## 源代码写入新文件
output_file = RTOS_json["generated_code_path"]
with open(output_file,"w") as f:
   f.write(generated_code)
print("finish code generation to {}".format(output_file))

## 判断 是否需要生成configration
if RTOS_json["Configration_templates"] == "":
   print("no need to generate configration file") 
## 否则 生成configration
else:
   print("generate configration")
   cfg_config={
    "active_core": args.core,
    "execution_loop": args.loop,
    "execution_step":args.step,
    "type":args.type,
    "pattern":args.pattern,
    "subpattern":args.subpattern }
   #获取路径
   cfg_path=RTOS_json["Configration_templates"]
   #加载环境
   env=Environment(loader=FileSystemLoader(os.getcwd()),lstrip_blocks=False) 
   #获取子模版
   if args.type==0:
      if args.pattern in [2,3,4,5]:
         pattern_path= cfg_path+"/Patterns/Workload_Nested.jinja"
      else: 
         pattern_path= cfg_path+"/Patterns/Workload_Single.jinja"
   elif args.type==1:
      pattern_path=cfg_path+"/Patterns/Scalability.jinja"
   else:
      print("error scenario type")
   #加入子模版
   cfg_config["cfg_pattern"]=pattern_path
   template = env.get_template(cfg_path+"/cfg_template.jinja")
   generated_cfg =template.render(cfg_config)
   output_file = RTOS_json["Configration_path"]
   with open(output_file,"w") as f:
      f.write(generated_cfg)
   print("finish configration generation to {}".format(output_file))




#### Part3: 调用子脚本执行cross compile

## 获取python子脚本路径

py_path=RTOS_json["compile"]
print(py_path)
command = ["python3", py_path, "--loop", str(args.loop), "--step", str(args.step), "--output", RTOS_json["output"]]
process = subprocess.Popen(command)
process.wait()
print("execution completed.")


#### Part4: 分析数据 （还没调整好）
## 获取文件
output_path = RTOS_json["output"]+"output.log"
df = read_and_process_file(output_path)
plot_histogram_as_lines(df)



'''
env_path = "/Users/xingxiansen/Exiao/XMOS_XTC_15.2.1/SetEnv.sh"  
env_command = f"source {env_path} && env"
process = subprocess.Popen(env_command, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")
stdout, _ = process.communicate()
env = os.environ.copy()
for line in stdout.decode().splitlines():
    key, _, value = line.partition("=")
    env[key] = value
print("environment set")

## 执行makefile
make_path = "/Users/xingxiansen/Exiao/Research/Xmos/freeRTOS/FreeRTOS/FreeRTOS/Demo/ThirdParty/Community-Supported-Demos/XCORE.AI_xClang/RTOSDemo"
output_path = RTOS_json["output"]
process=subprocess.Popen(
   "script output.log xrun --xscope bin/RTOSDemo.xe ",
    cwd=make_path,
    env=env,
    shell=True
)
print("running make run")

## 复制输出到output
time.sleep(args.loop*(100/args.step)+30)
print("output")
shutil.copy(make_path+"/output.log",RTOS_json["output"])




## 存在问题, 有屏幕输出但是没法读取, 同时串口也没法定位
应该是工具有自己占用串口的方法（chatgpt）
with open(output_path, "w") as output_file:
   process = subprocess.Popen(
      ["xrun", "--xscope","bin/RTOSDemo.xe"],
      cwd=make_path,
      env=env,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      universal_newlines=True,  # 逐行读取输出
      bufsize=1,  # 行缓冲模式
   )
   print("running make run")
   for line in process.stdout:
        print(line, end="")  # 打印到控制台
        output_file.write(line)  # 写入日志文件

## 打印输出


#### 备用函数
## 寻找串口
#ports = serial.tools.list_ports.comports()
#for port in ports:
#	print(f"device:{port.device},discription:{port.description}")

'''







		










