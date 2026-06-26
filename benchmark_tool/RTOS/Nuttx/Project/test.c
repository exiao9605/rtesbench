//头文件
#include <nuttx/semaphore.h>
#include <nuttx/clock.h>
#include <nuttx/config.h>
#include <nuttx/init.h>
#include <nuttx/sched.h>
#include <nuttx/arch.h>
#include <nuttx/syslog/syslog.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
//define预定义
#define active_core 1
#define Priority_High 80
#define Priority_Mid  50
#define Priority_Low  20
#define STACKSIZE   1024
#define secCNT  156000000
#define cntnSEC  6.41

#define QUEUE_NAME "/my_mq"
#define QUEUE_NAME2 "/my_mq2"

#define DEMCR           (*(volatile uint32_t*)0xE000EDFC)
#define DWT_CTRL        (*(volatile uint32_t*)0xE0001000)
#define DWT_CYCCNT      (*(volatile uint32_t*)0xE0001004)
#define DWT_CPICNT      (*(volatile uint32_t*)0xE0001008)
#define DWT_EXCCNT      (*(volatile uint32_t*)0xE000100C)
#define DWT_SLEEPCNT    (*(volatile uint32_t*)0xE0001010)
#define DWT_LSUCNT      (*(volatile uint32_t*)0xE0001014)
#define DWT_FOLDCNT     (*(volatile uint32_t*)0xE0001018)

#define DEMCR_TRCENA    (1 << 24)
#define DWT_CTRL_CYCCNTENA (1 << 0)
#define DWT_CTRL_CPIENA (1 << 17)
#define DWT_CTRL_EXCENA (1 << 16)
#define DWT_CTRL_SLEEPENA (1 << 18)
#define DWT_CTRL_LSUENA (1 << 20)
#define DWT_CTRL_FOLDENA (1 << 21)
//定义函数
void enable_dwt_cyccnt(void) {
    // Enable TRCENA in DEMCR
    DEMCR |= DEMCR_TRCENA;
    
    // Enable the cycle counter in DWT_CTRL
    DWT_CTRL |= DWT_CTRL_CYCCNTENA;
    DWT_CTRL |= DWT_CTRL_CPIENA;
    DWT_CTRL |= DWT_CTRL_EXCENA;
    DWT_CTRL |= DWT_CTRL_SLEEPENA;
    DWT_CTRL |= DWT_CTRL_LSUENA;
    DWT_CTRL |= DWT_CTRL_FOLDENA;
    
    // Reset the cycle counter value
    DWT_CYCCNT = 0;
    DWT_CPICNT = 0;
    DWT_EXCCNT = 0;
    DWT_SLEEPCNT = 0;
    DWT_LSUCNT = 0;
    DWT_FOLDCNT = 0;

}

uint32_t read_dwt_cyccnt(void) {
    return DWT_CYCCNT;
}
// 定义全局semaphore及其他
sem_t sem1;
sem_t sem2;int sem_val;
int sem_val2;
int policy;
struct sched_param param;
int break_flag_P2_obj=0;

pthread_cond_t cond1;
pthread_mutex_t mutex1;
pthread_cond_t cond2;
pthread_mutex_t mutex2;
int condition=0;

struct mq_attr attr_data_s;
struct mq_attr attr_data_s2;
char message1[100]="message";
char message2[100];
irqstate_t flags;int histogram[1001] = {0};
int Stress_Frequency=0;



// Target 函数
static void* task_target1(void* arg){

    //target task starts
    printf("Target task starts\n");   
    long start_time;
    long begin_time;
    long end_time;
    long duration;
    long execution_time;
    printf("task_stress %d Wait for affinity\n", core_id);
    while(1){
         if(up_cpu_index()==core_id)
            break;
    }
    enable_dwt_cyccnt();   
   
    //main loop
    while(Stress_Frequency<=100){
    	printf("Evaluation- %d starts\n",Stress_Frequency);
    	start_time=read_dwt_cyccnt();
    	while(1){

    		//measure the execution time of target
    		begin_time=read_dwt_cyccnt();
    		sem_getvalue(&sem1,&sem_val);       
            end_time=read_dwt_cyccnt();

            //duration calculation & write in histogram
            duration=(int)(end_cnt-begin_cnt)*cntnSEC;  
            if(duration/10<1000){
                  histogram[duration/10]++;
            }
            else histogram[1000]++;
            execution_time=(end_cnt-start_cnt)/secCNT; 
            //loop judge: print histogram and to next loop
            if(execution_time>=10){
            	long sum=0;
            	int cnt=0;
            	printf("print histogram for Frequency %d\n",Stress_Frequency);
            	for(int i=0;i<1000;++i){
            		if(histogram[i]!=0){
            			cnt+=histogram[i];
            			sum+=histogram[i]*i;
            			printf("%d : %d\n",i,histogram[i]);
            		}
            	}
            	printf(">1000 : %d\n", histogram[1000]);
            	if(cnt!=0){
            		printf("average execution time: %d\n",sum/cnt);
            	}
            	for(int i=0;i<=1000;++i){
            		histogram[i]=0;
            	}
            	break;
            }
    	}
    	Stress_Frequency+=10;
    } 
    printf("All evaluation endded, start after process");

    //after process of RTOS
	return 0;
}

// Stress 函数
static int task_stress(int argc, FAR char* argv[]){

	int core_id=(int)arg;
	printf("task_stress %d Wait for affinity\n", core_id);
    while(1){
         if(up_cpu_index()==core_id)
            break;
    }
	int rand;
	int seed=core_id*255;

	//stress task starts
	printf("StressTask-%d starts\n",core_id);
	while(Stress_Frequency<=100){
		rand= rand_r(&seed)%101;
		if(rand<Stress_Frequency){
			sem_getvalue(&sem1,&sem_val)
		}
		else{
			sem_getvalue(&sem2,&sem_val)
		}
	}
    
    printf("stress on core%d endded \n",core_id);
	//after process of RTOS
	return 0;
}

//Main 函数
int main(int argc, FAR char *argv[]){
    
    pthread_t pthreads[10];
   pthread_t pthread1;
   pthread_t pthread2;
   pthread_attr_t attr[10];
   pthread_attr_t attr1;
   pthread_attr_t attr2;
   cpu_set_t cpus;
   cpu_set_t cpu0;
    sem_init(&sem1,0,1);
sem_init(&sem2,0,1);
    printf("Test program start\n");
  
   for(int i=1;i<=active_core;++i){
       char task_name[20];
       snprintf(task_name,sizeof(task_name),"StressTask%d",i);
       pthread_create(&pthreads[i], &attr, task_stress, (void*)i);
       cpu_set_t cpuset;
       CPU_ZERO(&cpuset);
       CPU_SET(i,&cpuset);
       if(pthread_setaffinity_np(pthreads[i], sizeof(cpu_set_t),&cpuset) != 0) {
               printf("failed to set affinity for Task%d\n",i);      
      }
   } 
   printf("Finish Creating Stress Tasks");
   

   pthread_create(&pthread2, &attr, task_target, NULL);
   cpu_set_t cpuset;
   CPU_ZERO(&cpuset);
   CPU_SET(0,&cpuset);
   if(pthread_setaffinity_np(pthread2, sizeof(cpu_set_t),&cpuset) != 0) {
      printf("failed to set affinity for Main Task\n");      
   }
    printf("Finish Creating target Tasks\n");
   pthread_join(pthread2, NULL);
   printf("Main task exit\n");
   for(int i=1;i<=5;++i){
        pthread_join(pthreads[i], NULL);
        printf("Task %d exit\n", i);
   }

}


