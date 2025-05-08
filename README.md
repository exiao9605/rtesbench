# rtesbench
rtesbench: A Multi-core Benchmark Framework for Real-Time Embedded Systems

## rtesbench introduction
RTESBench is a benchmark tool for stress-testing RTOS APIs and reproducing cross-core contention scenarios. It helps evaluate the multicore performance and bottlenecks of embedded systems by simulating realistic workloads on different RTOS platforms.
rtesbench 对 RTOS的API进行压力测试，复现跨核竞争场景，用于评价多核嵌入式系统的多核性能特征以及瓶颈

## Usage
Use `python codeGenerator.py` to generate benchmarks.
**Parameters**
- o —— Target system to evaluate  (0-Nuttx 1-FreeRTOS 2-TOPPERS/FMP) 
- t —— Evaluation Mode   (0-workload 1-scalability) 
- p —— Benchmark Scenarios  (from API pattern1 to pattern6)
- sp —— sub partern  (for pattern4-1/4-2)
- c —— active cores (according to the hardware)

## Project Structure

├── Tool/                            
│   ├── codeGenerator.py              
│   └── Source/                       
│       ├── Benchmark/              
│       │   ├── Workload/            
│       │   └── Scalability/         
│       └── RTOS/                    
│           ├── RTOS 1/            
│           ├── RTOS 2/              
│           └── RTOS 3/             
│               ├── Configuration/    
│               ├── Project/        
│               ├── RTOStemplate/    
│               ├── System/          
│               └── Output/          
