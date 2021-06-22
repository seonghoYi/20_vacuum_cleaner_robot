#define F_CPU 8000000UL			//8M로 동작 
#include <util/delay.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdio.h>

/* 젯슨나노가 ATmega328에게 명령했을 때 젯슨나노는 ATmega328이 명령을 수행완료했는지 알 수 없다.
젯슨나노와 ATmega328 사이에는 인터럽트가 3가지 존재한다. 
인터럽트핀은 하나이므로 인터럽트 종류를 알려주기위해 인터럽트 상태변수 선언*/
volatile unsigned char intstatus = 0x00;
// 0x01: bluetooth interrupt
// 0x02: target move complete interrupt
// 0x03: target moving stop interrupt


#define SETB(PORT, BIT) (PORT) |= (BIT)		// 해당 PORT의 해당 BIT set 하는 함수매크로 
#define CLRB(PORT, BIT) (PORT) &= ~(BIT)	// 해당 PORT의 해당 BIT clear 하는 함수매크로

#define SETINT SETB(INT_PORT, INT) //(AVR_INT핀) 인터럽트핀 켜기 
#define CLRINT CLRB(INT_PORT, INT) //(AVR_INT핀) 인트럽트핀 끄기




/****************************************SUCTION***************************************/
void BLDCOn(){		 //흡입모터 on
	PORTD |= 0x80;   //PORTD의 8번째 핀을 ENABLE함 
}

void BLDCOff(){		 //흡입모터 off
	PORTD &= ~0x80;  //PORTD의 8번째 핀을 DISABLE함
}

void BLDCInit(){	//흡입모터 초기화
	DDRD |= 0x80;	//GPIO PD7을 OUTPUT으로 설정
	PORTD &= ~0x80; //PD7의 값을 0으로 초기화
}


/****************************************SUCTION_END***************************************/



/****************************************Bluetooth***************************************/
#define BT_DDR DDRB 
#define BT_PORT PORTB
#define BT_CFG 0x01  
#define BT_RST 0x02
#define INT_DDR DDRB
#define INT_PORT PORTB
#define INT 0x04

volatile int bt_cnt, bt_read_cnt;
volatile char bt_data[6];


void Serial0Baud(unsigned long baud);
void Serial0Init(unsigned long baud);
void BTAtSet(char mode);
char Rx0Char();
void Tx0Char(char tx_data);
void Tx0String(char *str);
void TxAxis(unsigned int X, unsigned int Y);

void Serial0Baud(unsigned long baud) //baudrate 설정
{
	float ubrr_f;
	unsigned int ubrr;
	// ubrr_f = (float)F_CPU / (16.0 * (float)baud) - 1.0 + 0.5 반올림하기 위해 0.5를 더함
	/* 실수형에서 정수형 형변환을 할 경우에 소수점을 버린다.
	예시) 
	① Baud Rate = 38.4k => ubrr_f = 12.02 => ubrr = 12
	datasheet의 UBRR과 동일하다. 
	② Baud Rate = 14.4k => ubrr_f = 33.72 => ubrr = 33이 된다.
	datasheet를 보면 UBRR은 34가 되어야한다. 형변환 시 소수점은 버림처리되기 때문에 0.5를 더하여 반올림을 해준다.
	*/
	ubrr_f = (float)F_CPU / (16.0 * (float)baud) - 0.5;
	ubrr = ubrr_f; 
	UBRR0H = (ubrr >> 8) & 0xFF; //UBRR0H에 ubrr의 상위 8비트를 대입한다.
	UBRR0L = ubrr & 0xFF; //UBRR0L에 ubrr의 하위 8비트를 대입한다.
}
void SendInt()// BT수신 시 INT발생
{
	SETB(INT_PORT ,INT);
}

void BTAtSet(char mode) // mode : 0 Slave, 1 Master
{
	UCSR0B = 0x18;			//5번째 비트(수신부 동작 활성화),4번째 비트(송신부 동작 활성화) 활성화
	Serial0Baud(38400);		// 통신속도 설정
	SETB(BT_PORT, BT_CFG);	// AT 설정 
	CLRB(BT_PORT, BT_RST);	// 블루투스 리셋
	_delay_ms(10);
	SETB(BT_PORT, BT_RST);
	if (mode == 1) // 블루투스 master 모드
	{
		_delay_ms(500);
		Tx0String("AT+NAME=CLEAN\r\n"); //블루투스 이름 설정
		_delay_ms(500);
		Tx0String("AT+PSWD=gsr\r\n");	//블루투스 비밀번호 설정
		_delay_ms(500);
		Tx0String("AT+UART=38400,0,0\r\n"); //Baud Rate 설정
		_delay_ms(500);
		Tx0String("AT+ROLE=1\r\n"); //마스터,슬레이브 설정 
		_delay_ms(500);
		Tx0String("AT+INIT\r\n");	//기초 설정
		_delay_ms(500);		
		Tx0String("AT+PAIR=");		//블루투스 페어링
		// datasheet 참고 AT+PAIR = <Param1>,<Param2>
		Tx0String("2020,5,171539"); //운반 로봇 주소 <Param1 : Device Address>
		Tx0String(",20\r\n"); //페어링 Time Out 20초 <Param2 : Time out>
		_delay_ms(500);
	}
	else if (mode == 0) // 블루투스 slave 모드
	{
		_delay_ms(500);
		Tx0String("AT+NAME=CLEAN\r\n");  //블루투스 이름 설정 
		_delay_ms(500);
		Tx0String("AT+PSWD=gsr\r\n"); //블루투스 비밀번호 설정
		_delay_ms(500);
		Tx0String("AT+UART=38400,0,0\r\n"); //Baud Rate 설정
		_delay_ms(500);
		Tx0String("AT+ROLE=0\r\n"); //마스터,슬레이브 설정
		_delay_ms(500);
		Tx0String("AT+INIT\r\n"); //기초 설정
	}
	_delay_ms(1000);
	Serial0Baud(38400);
	
	CLRB(BT_PORT, BT_CFG);  // AT설정 종료
	CLRB(BT_PORT, BT_RST);  //블루투스 리셋
	_delay_ms(10);
	SETB(BT_PORT, BT_RST);
	
	UCSR0B = 0x98; //8번째 비트도 활성화 (활성화시 수신완료 인터럽트 발생)
}



char Rx0Char() // Serial0를 이용하여 데이터 수신 
{
	while (!(UCSR0A & 0x80)); //데이터를 수신 받을 때까지 대기
	return UDR0; //수신받은 데이터를 반환
}

void Tx0Char(char tx_data) // Serial0를 이용하여 데이터 송신
{
	while (!(UCSR0A & 0x20)); //데이터 버퍼가 비워질 때까지 대기
	UDR0 = tx_data; //송신할 데이터 입력
}

void Tx0String(char *str)   //Serial0를 이용하여 문자열을 송신
{
	while (*str)			//포인터를 이용하여 문자열에 NULL문자를 만날 때까지 반복
	Tx0Char(*str++);		//문자열의 문자를 하나씩 순서대로 송신
}

void TxAxis(unsigned int X, unsigned int Y)
{
	//ATmega328에서 int형은 16bit고 Tx0(char)는 8bit로 전송한다. 
	Tx0Char((char)(X >> 8));	//X의 상위비트를 전송
	Tx0Char((char)(X & 0xFF));	//X의 하위비트를 전송
	Tx0Char((char)(Y >> 8));	//Y의 상위비트를 전송
	Tx0Char((char)(Y & 0xFF));	//Y의 하위비트를 전송
}

ISR(USART_RX_vect)
{
	bt_data[bt_cnt++] = UDR0;	//수신된 데이터를 버퍼에 넣는다.
	intstatus = 0x01;			//인터럽트 상태 설정
	SETINT;						//인터럽트핀 활성화
}

void Serial0Init(unsigned long baud)//송수신 on rxint on
{
	UCSR0A = 0x00;	//상태레지스터 초기화
	UCSR0B = 0x98;	//interrupt 10000000 : Rx complete  01000000 : Tx complete  00100000 : UDR Empty
	UCSR0C = 0x06;	//8bit 데이터 송수신 설정
	Serial0Baud(baud); //보레이트 설정
	SETB(BT_DDR, BT_CFG | BT_RST);
	SETB(INT_DDR, INT);
	CLRB(BT_PORT, BT_RST);
	_delay_ms(10);
	SETB(BT_PORT, BT_RST);
}


/****************************************Bluetooth end***************************************/



/****************************************Step***************************************/
#define STEP_DDR	DDRD
#define STEP_PORT	PORTD		
#define STEP_EN		0x04		//Active low로 동작한다.
#define STEP_LCLK	0x08
#define STEP_LDIR	0x10
#define STEP_RCLK	0x20
#define STEP_RDIR	0x40

#define STEP_L_DIR_FOR	SETB(STEP_PORT, STEP_LDIR)	// 왼쪽모터의 방향 결정(CW, CCW) 
#define STEP_L_DIR_BACK	CLRB(STEP_PORT, STEP_LDIR)
#define STEP_R_DIR_BACK	CLRB(STEP_PORT, STEP_RDIR)	// 오른쪽모터의 방향 결정(CW, CCW) 
#define STEP_R_DIR_FOR	SETB(STEP_PORT, STEP_RDIR)
#define STEP_EN_ON		CLRB(STEP_PORT, STEP_EN)	
#define STEP_EN_OFF		SETB(STEP_PORT, STEP_EN)


volatile int X_axis, Y_axis;
volatile int X_axis_rel, Y_axis_rel;
volatile unsigned int STEP_right_speed, STEP_left_speed;	//로봇의 속도를 조절하기 위한 변수
volatile unsigned char cnt_toggle, cnt_dir, mot_dir[2];		// 0 : L, 1 : R
volatile unsigned char relative_toggle;
volatile unsigned int relative_target;
//----------TIMER0_OVF----------//
void enable_TIMER0_ovf()
{
	TCCR0B |= 0x04;			// 분주비 256
	TIMSK0 |= 0x01;			// 타이머0를 인터럽트로 사용한다.
}
void disable_TIMER0_ovf()
{
	TIMSK0 &= ~0x01;
	TCCR0B &= ~0x04;
}
//----------TIMER2_OVF----------//
void enable_TIMER2_ovf()
{
	TCCR2B |= 0x06;			// 분주비 256
	TIMSK2 |= 0x01;			// 타이머2를 인터럽트로 사용한다. 
}
void disable_TIMER2_ovf()
{
	TIMSK2 &= ~0x01;
	TCCR2B &= ~0x06;
}

void StepMotorStop();

ISR(TIMER0_OVF_vect)		// Right motor control
{
	TCNT0 = STEP_right_speed;
	STEP_PORT ^= STEP_RCLK;
	if(cnt_toggle) // 좌표를 카운트할 때 
	{
		switch(cnt_dir) // cnt_dir => 0: x 축으로 증가하는 방향, 1: y 축으로 감소하는 방향, 2: x 축으로 감소하는 방향, 3: y 축으로 증가하는 방향
		{
			case 0:
			if(mot_dir[0] == 0) // 전진일 때 0, 후진일 때 1 (회전일 경우는 제외하기 때문에 2개의 모터 중 하나로만 비교해도 상관없다.)
			{
				X_axis++;
			}
			else  
			X_axis--;
			break;
			
			case 1:
			if(mot_dir[0] == 0)
			Y_axis--;
			else
			Y_axis++;
			break;
			
			case 2:
			if(mot_dir[0] == 0)
			X_axis--;
			else
			X_axis++;
			break;
			
			case 3:
			if(mot_dir[0] == 0)
			Y_axis++;
			else
			Y_axis--;
			break;
		}
		if(relative_toggle) // 목표지점까지 이동할 때 
		{
			switch(cnt_dir) // cnt_dir => 0: x 축으로 증가하는 방향, 1: y 축으로 감소하는 방향, 2: x 축으로 감소하는 방향, 3: y 축으로 증가하는 방향
			{
				case 0:
				if(mot_dir[0] == 0) // 전진일 때 0, 후진일 때 1 (2개의 모터 중 하나로만 비교해도 상관없다. 회전일 경우는 제외한다.)
				{
					if((X_axis - X_axis_rel) >= relative_target){ // X_axis_rel : 시작시 점, X_axis : 움직인 점, relative_target : 목표 지점 
						StepMotorStop();	// 스텝모터 멈춘다.
						intstatus = 0x02; // target move complete interrupt
						SETINT; //인터럽트 발생
					}
				}
				else 
				{
					if((X_axis_rel - X_axis) >= relative_target){ 
						StepMotorStop();
						intstatus = 0x02;
						SETINT;
					}
				}
				break;
				
				case 1:
				if(mot_dir[0] == 0)
				{
					if((Y_axis_rel - Y_axis) >= relative_target){
						StepMotorStop();
						intstatus = 0x02;
						SETINT;
					}
				}
				else
				{
					if((Y_axis - Y_axis_rel) >= relative_target){
						StepMotorStop();
						intstatus = 0x02;
						SETINT;
					}
				}
				break;
				
				case 2:
				if(mot_dir[0] == 0)
				{
					if((X_axis_rel - X_axis) >= relative_target){
						StepMotorStop();
						intstatus = 0x02;
						SETINT;
					}
				}
				else
				{
					if((X_axis - X_axis_rel) >= relative_target){
						StepMotorStop();
						intstatus = 0x02;
						SETINT;
					}
				}
				break;
				
				case 3:
				if(mot_dir[0] == 0)
				{
					if((Y_axis - Y_axis_rel) >= relative_target){
						StepMotorStop();
						intstatus = 0x02;
						SETINT;
					}
				}
				else
				{
					if((Y_axis_rel - Y_axis) >= relative_target){
						StepMotorStop();
						intstatus = 0x02;
						SETINT;
					}
				}
				break;
			}
		}
	}
}

ISR(TIMER2_OVF_vect)		// Left motor control
{
	TCNT2 = STEP_left_speed;
	STEP_PORT ^= STEP_LCLK;
}

void StepSpeed(char R_speed, char L_speed)	//바퀴 속도 결정
{
	STEP_right_speed = R_speed;
	STEP_left_speed = L_speed;
}


void StepMotorConfig(char count, char dir, char R_dir, char L_dir){ 
	mot_dir[0] = L_dir; // 왼쪽 방향 설정 0이면 전진, 1이면 후진 
	mot_dir[1] = R_dir; // 오른쪽 방향 설정 0이면 전진, 1이면 후진 
	cnt_toggle = count; // 0이면 카운트 안하고 1이면 카운트 한다. 
	cnt_dir = dir;		// 방향(0~3)으로 구분한다.
}

void StepMotorStart()	//speed, dir : 0 ~ 1
{
	//----------스텝모터 설정----------//
	STEP_EN_ON; // 스텝 모터 활성화 
	//-------바퀴 회전 방향 결정-------//
	/* 구조상 2개의 모터가 등을 지고있어서 방향이 다르다.
	따라서 전진일 경우 왼쪽방향은 반시계 오른쪽은 시계로 해야 전진한다.*/
	switch (mot_dir[0]) //왼쪽 방향 
	{
		case 0: // 전진
		STEP_R_DIR_BACK; 
		break;
		case 1: // 후진
		STEP_R_DIR_FOR;
		break;
	}
	switch (mot_dir[1]) //오른쪽 방향 
	{
		case 0: // 전진
		STEP_L_DIR_FOR;
		break;
		case 1: // 후진 
		STEP_L_DIR_BACK;
		break;
	}
	enable_TIMER0_ovf(); // 타이머0 활성화 
	enable_TIMER2_ovf(); // 타이머2 활성화 
}

void StepMotorStop()
{
	disable_TIMER0_ovf(); // 타이머0 비활성화
	disable_TIMER2_ovf(); // 타이머2 비활성화
	_delay_ms(200);		  // 관성으로 인한 오차를 막기위한 딜레이
	STEP_EN_OFF; // 스텝 모터 비활성화 
}

void StepInit()
{
	STEP_DDR |= STEP_EN | STEP_LCLK | STEP_LDIR | STEP_RCLK | STEP_RDIR; // 사용할 포트 설정
	STEP_PORT |= STEP_EN; 
}


/****************************************Step end***************************************/

/****************************************ADC***************************************/

/*	PSD0	PSD1	PSD2	PSD3	PSD4	*/
/*	PC0		PC1		PC2		PC3		PC4		*/

volatile unsigned int PSD_buf[8];
volatile unsigned int PSD[6];// ADC0 ADC1 ADC2 ADC3 ADC6 ADC7
volatile unsigned int prev_PSD[6];// ADC0 ADC1 ADC2 ADC3 ADC6 ADC7
volatile unsigned int Threshold[5];// 500, 450, 400, 350, 300
volatile int adc_num, adc_idx = 0;
volatile char adc_flag = 0;

void ADCInit()//PSD센서 초기화 - ADC 사용
{
	ADMUX = 0x40; // AVCC를 기준전압으로 사용한다.
	ADCSRA = 0xCF; // ADEN:1, ADSC:1, ADIE: 1,ADPS(0~2): 분주비 128로 설정
}

ISR(ADC_vect)
{
	PSD_buf[adc_num] = ADC; // ADC : 데이터 레지스터, ADC 0~7까지는 읽는다. 
	
	ADMUX &= ~0x0F;		// 하위 3비트만 사용한다. (ADC 8 온도센서용이라 쓰지는 않는다.)
	ADMUX |= ++adc_num; // 다음에 읽을 ADC 포트를 설정한다. 

	if(adc_num == 8)	// ADC 7까지 다 읽었을 경우
	{
		adc_num = 0;	// adc_num을 0으로 초기화한다. 
		ADMUX &= ~0x0F; // 하위 비트 초기화한다.
		
		// 이전의 값을 누적하는 것이 아닌 LPF를 구간별로 필터하기 위해 adc_flag가 0이면 이전의 PSD값에 넣고, 1이면 현재의 PSD값에 넣는다. 
		if (adc_flag == 0){   
			prev_PSD[0] = PSD_buf[0]; // PC4(ADC4)와 PC5(ADC5)는 I2C 포트로 사용해서 값만 읽고 쓰지는 않는다.
			prev_PSD[1] = PSD_buf[1];
			prev_PSD[2] = PSD_buf[2];
			prev_PSD[3] = PSD_buf[3];
			prev_PSD[4] = PSD_buf[6];
			prev_PSD[5] = PSD_buf[7];
			adc_flag = 1;
		}
		else if(adc_flag == 1){
			PSD[0] = PSD_buf[0];	
			PSD[1] = PSD_buf[1];
			PSD[2] = PSD_buf[2];
			PSD[3] = PSD_buf[3];
			PSD[4] = PSD_buf[6];
			PSD[5] = PSD_buf[7];
			adc_flag = 0;
		}
		// 디지털 LPF 구성
		for(int i = 0; i < 6; i++){ 
			if ((PSD[i] - prev_PSD[i]) > 10){ // 현재의 PSD값(PSD[i])과 이전의 PSD값(prev_PSD[i])이 10 이상 차이나는지 확인
				PSD[i] = prev_PSD[i] + 10; // 이전의 PSD값에 임의로 10을 더해서 현재의 PSD값으로 한다.
				PSD[i] = prev_PSD[i] * 0.98 + PSD[i] * 0.02; // 이전의 PSD값의 98%, 현재의 PSD값 2%의 비율로 현재의 PSD값에 반영한다 
			}
		}
		
		/* 
		Threshold[i]를 통해 PSD 값이 특정의 값을 넘었는지 비트로 표시한다.  
		(Threshold[4]:500, Threshold[3]:450, Threshold[2]:400, Threshold[1]:350, Threshold[0]:300)
		ex) 
		① PSD1(비트1) : 320 
		   => Threshold[0] => 2 => 0000 0010 => PSD1의 값이 300을 넘었다.
		② PSD0(비트0) : 380 
		   => Threshold[0] => 1 => 0000 0001 => PSD0의 값이 300을 넘었다.
		   => Threshold[1] => 1 => 0000 0001 => PSD0의 값이 350을 넘었다.
		*/
		for(int i = 0 ; i < 5; i++) 
		{
			Threshold[i] = 0;
			for(int j = 0 ; j < 6; j++)
			{
				if(PSD[j] >= (10 - i) * 50)
				Threshold[i] |= 1 << j;
			}
		}
	}
	
	ADCSRA |= 0x40; //변환 시작
	
	
	
}

/****************************************ADC end***************************************/

/****************************************I2C***************************************/
#define SUCTIONSECTION	0x00  
#define SUCTIONMOTOROFF	0x00	//흡입모터 off 커맨드
#define SUCTIONMOTORON	0x01    //흡입모터 on 커맨드
#define PSDSECTION		0x10
#define PSDRAWDATA0		0x10
#define PSDRAWDATA1		0x11
#define PSDRAWDATA2		0x12
#define PSDRAWDATA3		0x13
#define PSDRAWDATA4		0x14
#define PSDRAWDATA5		0x15
#define PSDTHRES500		0x16
#define PSDTHRES450		0x17
#define PSDTHRES400		0x18
#define PSDTHRES350		0x19
#define PSDTHRES300		0x1A
#define BTSECTION		0x20
#define BTJETTOAVR		0x20
#define BTAVRTOJET		0x21
#define BTATSLAVE		0x22
#define BTATMASTER		0x23
#define STEPSECTION		0x30
#define STEPCFG			0x30
#define STEPSTART		0x31
#define STEPSTOP		0x32
#define STEPLEFTSPEED	0x33
#define STEPRIGHTSPEED	0X34
#define STEPXCOUNTH		0x35
#define STEPXCOUNTL		0x36
#define STEPYCOUNTH		0x37
#define STEPYCOUNTL		0x38
#define STEPTARGETH		0x39
#define STEPTARGETL		0x3A
#define INTSECTION		0x40
#define INTSTATUS		0x40


#define SR_SLA_ACK		0x60	
#define SR_DATA_ACK		0x80
#define SR_DATA_NACK	0x88
#define SR_STOP			0xA0

#define ST_SLA_ACK		0xA8
#define ST_DATA_ACK		0xB8
#define ST_DATA_NACK	0xC0
#define ST_LAST_DATA	0xC8
#define SCL				400000UL


volatile int reg = 0;
volatile int flag = 0;
volatile unsigned char data = 0;
volatile int X_axis_buf, Y_axis_buf;

ISR(TWI_vect){
	switch(TWSR){
		//slave receive
		case SR_SLA_ACK :
		flag = 0; // 명령어의 종류와 데이터를 구분하기 위해 사용하는 플래그
		TWCR = (1<<TWINT)|(1<<TWEA)|(1<<TWEN)|(1<<TWIE); // ACK 송신
		break;
		case SR_DATA_ACK:
		if(flag == 0){	// 플래그 0 : 명령어의 종류를 받을 때
			reg = TWDR; // TWDR로부터 명령어의 종류를 수신받는다.
			flag = 1;	// 플래그를 1로 변경
			TWCR = (1<<TWINT)|(1<<TWEA)|(1<<TWEN)|(1<<TWIE); // ACK 송신
		}
		else if(flag == 1){ // 플래그 1 : 데이터를 송신할 때
			if((reg & 0xF0) == SUCTIONSECTION){		//상위4비트로 명령의 종류 확인 
				if(reg == SUCTIONMOTORON){			//흡입모터 on 명령을 받았을 때 
					data = TWDR;					//쓰레기 데이터 처리
					BLDCOn();						//흡입모터를 킨다.
					flag = 0;						//다음 통신을 위해 플래그 초기화
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
				else if(reg == SUCTIONMOTOROFF){	// 흡입모터 off 명령을 받았을 때
					data = TWDR;					//쓰레기 데이터 처리
					BLDCOff();						//흡입모터를 끈다.
					flag = 0;						//다음 통신을 위해 플래그 초기화
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
			}
			else if((reg & 0xF0) == BTSECTION){
				if(reg == BTJETTOAVR){ //젯슨에서 블루투스로 데이터를 송신하는 기능
					data = TWDR; // 송신할 데이터
					Tx0Char(data); // 블루투스 모듈로 송신
					flag = 0; //다음 통신을 위해 flag 초기화
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
				else if(reg == BTATMASTER){ // 블루투스 모듈을 마스터로 설정
					data = TWDR; //쓰레기 데이터 처리
					BTAtSet(1); //1 넣으면 마스터. 0 슬레이브
					flag = 0; //다음 통신을 위해 flag 초기화
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
				else if(reg == BTATSLAVE){ // 블루투스 모듈을 슬레이브로 설정
					data = TWDR; //쓰레기 데이터 처리
					BTAtSet(0); //1 넣으면 마스터. 0 슬레이브
					flag = 0; //다음 통신을 위해 flag 초기화
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
			}
			else if((reg & 0xF0) == STEPSECTION){ // 스텝모터 동작과 관련된 기능 처리문
				if(reg == STEPCFG){ // 스텝모터 설정
					data = TWDR; // 수신된 데이터 저장
					flag = 0; //다음 통신을 위해 flag 초기화
					StepMotorConfig((data >> 4) & 0x01, (data >> 2) & 0x03, data & 0x01, (data >> 1) & 0x01); //char count, char dir, char R_dir, char L_dir
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
				else if(reg == STEPSTART){ // 스텝모터 기동
					data = TWDR; //쓰레기 데이터 처리
					flag = 0; //다음 통신을 위해 flag 초기화
					StepMotorStart();
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
				else if(reg == STEPSTOP){ // 스텝모터 정지
					data = TWDR; //쓰레기 데이터 처리
					flag = 0; //다음 통신을 위해 flag 초기화
					StepMotorStop();
					if(relative_toggle == 1){  //relative_toggle이 1이라는것은 목표한 지점까지 이동하던 도중에 멈춘것이니 알려줘야함.
						intstatus = 0x03;
						SETINT;
					}
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
				else if(reg == STEPLEFTSPEED){ // 왼쪽 스텝모터 속도 설정
					data = TWDR; // 수신된 데이터 저장
					STEP_left_speed = data; // TCNT0 설정
					flag = 0; //다음 통신을 위해 flag 초기화
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
				else if(reg == STEPRIGHTSPEED){ // 왼쪽 스텝모터 속도 설정
					data = TWDR; // 수신된 데이터 저장
					STEP_right_speed = data; //TCNT2 설정
					flag = 0; //다음 통신을 위해 flag 초기화
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
				else if(reg == STEPTARGETH){ // 이동 목표 스텝 수 상위바이트 설정
					data = TWDR; // 수신된 데이터 저장
					relative_target = data; // 상위바이트지만 버퍼로 사용
					flag = 0; //다음 통신을 위해 flag 초기화
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
				else if(reg == STEPTARGETL){ // 이동 목표 스텝 수 하위바이트 설정
					data = TWDR; // 수신된 데이터 저장
					if(relative_target == 0x00 && data == 0x00)
						relative_toggle = 0; // 여태 수신된 데이터가 모두 0이라면 정지 명령이 있을 때까지 이동하는 것임
					else
					{
						relative_toggle = 1; // 그렇지 않다면 목표 장소까지 이동하는 것임
						X_axis_rel = X_axis; // 현재 위치를 저장
						Y_axis_rel = Y_axis; // 현재 위치를 저장
						relative_target = (relative_target << 8) | data;  // 상위 바이트와 하위 바이트를 조합하여 16비트 정수값으로 저장함
					}
					flag = 0; //다음 통신을 위해 flag 초기화
					TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
				}
			}
		}
		break;
		case SR_DATA_NACK :
		TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE); // 종료 루틴
		break;
		case SR_STOP:
		TWCR = (1<<TWINT)|(1<<TWEA)|(1<<TWEN)|(1<<TWIE); // 통신 사이클 초기화
		break;
		
		// i2c 1바이트 보낼 수 있다.(싱글 바이트 모드)
		

		//slave transmit
		case ST_SLA_ACK: //i2c 는 슬레이브가 마스터한테 함부로 데이터를 보내줄 수 없다.
		if((reg & 0xF0) == PSDSECTION){
			// 10비트를 8비트로 바꾸기 위해함.(기준전압(Vref) 3.3V 기준) psd 값 원래 1~1000정도 정도인데 나누기 4를 한다.
			if(reg == PSDRAWDATA0){
				TWDR = (unsigned char)(PSD[0] >> 2);  
			}
			else if(reg == PSDRAWDATA1){
				TWDR = (unsigned char)(PSD[1] >> 2);
			}
			else if(reg == PSDRAWDATA2){
				TWDR = (unsigned char)(PSD[2] >> 2);
			}
			else if(reg == PSDRAWDATA3){
				TWDR = (unsigned char)(PSD[3] >> 2);
			}
			else if(reg == PSDRAWDATA4){
				TWDR = (unsigned char)(PSD[4] >> 2);
			}
			else if(reg == PSDRAWDATA5){
				TWDR = (unsigned char)(PSD[5] >> 2);
			}
			else if(reg == PSDTHRES500){ //500 넘는지 확인 psd 6개 각 1비트로 대응함. 
				TWDR = Threshold[0];
			}
			else if(reg == PSDTHRES450){
				TWDR = Threshold[1];
			}
			else if(reg == PSDTHRES400){
				TWDR = Threshold[2];
			}
			else if(reg == PSDTHRES350){
				TWDR = Threshold[3];
			}
			else if(reg == PSDTHRES300){
				TWDR = Threshold[4];
			}
		}
		else if((reg & 0xF0) == BTSECTION){
			if(reg == BTAVRTOJET){ // 블루투스 데이터 수신
				TWDR = bt_data[bt_read_cnt++]; // 수신된 데이터를 마스터에게 전송
				if(bt_cnt == bt_read_cnt) // 저장된 데이터의 수와 읽은 데이터의 수가 같다면
				{
					CLRINT; // 인터럽트 클리어
					intstatus = 0;
					bt_cnt = 0;
					bt_read_cnt = 0;
					// 버퍼 상태 초기화
				}
			}
		}
		else if((reg & 0xF0) == STEPSECTION){
			X_axis_buf = X_axis;
			Y_axis_buf = Y_axis;
			if(reg == STEPLEFTSPEED){
				TWDR = STEP_left_speed; // 현재 설정된 속도값(TCNT0)을 송신
			}
			else if(reg == STEPRIGHTSPEED){
				TWDR = STEP_right_speed; // 현재 설정된 속도값(TCNT2)을 송신
			}
			else if(reg == STEPXCOUNTH){
				TWDR = (char)(X_axis_buf >> 8); // 현재 x 좌표 위치의 상위바이트 전송
			}
			else if(reg == STEPXCOUNTL){
				TWDR = (char)((X_axis_buf) & 0xFF); // 현재 x 좌표 위치의 하위바이트 전송
			}
			else if(reg == STEPYCOUNTH){
				TWDR = (char)(Y_axis_buf >> 8); // 현재 y 좌표 위치의 상위바이트 전송
			}
			else if(reg == STEPYCOUNTL){
				TWDR = (char)((Y_axis_buf) & 0xFF); // 현재 y 좌표 위치의 하위바이트 전송
			}
		}
		else if((reg & 0xF0) == INTSECTION){
			if(reg == INTSTATUS){ // 인터럽트 상태 송신
				TWDR = intstatus;
				if(intstatus == 0x02)
					CLRINT;
				else if(intstatus == 0x03)
					CLRINT;
				// 블루투스 인터럽트의 경우 상술한 동작이 따로 존재하므로 여기서는 자동으로 인터럽트를 초기화하지 않는다.
			}
		}
		TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
		break;
		case ST_DATA_ACK:
		TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWIE);
		break;
		case ST_DATA_NACK:
		case ST_LAST_DATA:
		TWCR = (1<<TWINT)|(1<<TWEA)|(1<<TWEN)|(1<<TWIE); // 통신 사이클 초기화
		break;
		default:
		break;
	}
}

void TWI_slave_init(char slave_addr){
	
	TWAR = slave_addr << 1; // 슬레이브 주소 설정 (7비트)
	TWAMR = 0x00; // 슬레이브 하위 주소 설정(ATMEGA 328에만 존재하고 여기서는 사용하지 않음)
	TWCR = (1<<TWEA)|(1<<TWEN)|(1<<TWIE); // 통신을 시작하기 위한 준비
}

/****************************************I2C end***************************************/



void SysInit(){
	Serial0Init(38400);
	/*
		이 시스템에서 시스템 클럭은 8MHz를 사용한다.
		atmega328의 데이터시트를 보면 시스템 클럭에 따른 보레이트 별 에러율이 제시되어있는데 일반적으로 임베디드에서 많이 사용하는 115200은 에러율이 커서 별도의 처리가 필요하게 되어 복잡해진다.
		대신 38400은 에러율이 별로 높지 않은 특징을 지니고 있어서 38400을 사용하게 되었다.
		HC-05의 기본 통신속도가 38400이기도 하다.
	*/
	StepInit();
	BLDCInit();
	ADCInit();
	TWI_slave_init(0x40); // 슬레이브 주소 0x40
	X_axis = 0;
	Y_axis = 0;
	_delay_ms(3000); // 자이로센서의 초기화 시간을 위한 딜레이
	sei(); // 전역 인터럽트 활성화
}

int main(void)
{
	SysInit();	//초기화
	BTAtSet(1);	//블루투스 모듈 마스터로 설정
	CLRINT;
	intstatus = 0x00; 
	bt_cnt = 0;
	/*
		HC-05 블루투스 모듈의 AT 커맨드는 명령어를 정상적으로 수신하거나 에러가 발생했을 때 "OK/r/n" 또는 "errorN/r/n"을 송신한다.(N은 에러코드)
		따라서 여기서 설정한 수신 데이터 버퍼에 상술한 문자열 데이터가 저장되는데 시스템 동작에 따르면 인터럽트 핀을 활성화시키고 intstatus에 0x01 코드를 지정하게 된다,
		그러나 이는 시스템에서 의도하는 동작이 아니므로 인터럽트를 초기화하고 intstatus 를 초기화한다. 또한 bt_cnt 를 0으로 초기화함으로써 수신 데이터 버퍼를 초기화하게 된다.
	*/
	_delay_ms(1000); // 페어링 대기
	
    while (1) 
    {

    }
}

