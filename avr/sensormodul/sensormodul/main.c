#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>
#include <util/delay.h>
#include <math.h>

struct Sensordata
{
	uint8_t ir_left;
	uint8_t ir_right;
	uint8_t ir_front;
	uint8_t gyro;
	uint8_t odometer_h;
	uint8_t odometer_l;
	uint8_t automatic_drive;
	uint8_t start_drive;
};

ISR(INT0_vect);
ISR(INT1_vect);
ISR(INT2_vect);
ISR(ADC_vect);
ISR(TWI_vect);

volatile uint8_t SLAVE_ADDRESS = 0x24;	// Slave address for TWI
volatile uint8_t analog_selected;		// Selected channel for ADC
volatile uint8_t adc_flag;				// Flag for ADC
volatile uint16_t odo_cnt;				// Global counter for odometer
volatile struct Sensordata sensor_data; // Sensordata
volatile uint8_t chosen_data = -1;		// Current chosen data to send on TWI

// 6.5 == 79

volatile uint8_t twi_data = -1;

// Initialized DDR
void init_ddr()
{

	// Init pins
	DDRA = 0x00;
	DDRB = 0x00;
	DDRC = 0x00;
	DDRD = 0x00;

	// Set pullup resistors
	PORTB = 0xFF;
	PORTC = 0xFF;
	PORTD = 0xFF;
}

// Initializes external interrupt
void init_interrupts()
{
	// INT0
	EICRA |= (1 << ISC01) | (1 << ISC00); // Interrupt on rising edge of INT0-pin.
	EIMSK |= (1 << INT0);				  // Enable external interrupts on INT0-pin

	// INT1
	EICRA |= (1 << ISC11) | (1 << ISC10); // Interrupt on rising edge of INT1-pin.
	EIMSK |= (1 << INT1);				  // Enable external interrupts on INT1-pin

	EICRA |= (1 << ISC21) | (1 << ISC20);
	EIMSK |= (1 << INT2);

	sei(); // Enable global interrupts
}

void init_twi()
{
	TWAR = (SLAVE_ADDRESS << 1); // Set slave address (7 bits with 0 as last)
	TWCR = (1 << TWIE) | (1 << TWEN) | (1 << TWEA);
}

// Initializes AD-conversion
void init_adc()
{
	ADCSRA = (1 << ADEN) | (1 << ADIE) | (0 << ADPS2) | (1 << ADPS1) | (0 << ADPS0); // Enable AD-converter, enable interrupts and set pre-scaler
	ADMUX = (0 << REFS0) | (0 << REFS1) | (1 << ADLAR);								 // Set the reference voltage and left shift
}

// Get left IR
void get_ir_left()
{
	adc_flag = 1;		 // Set ADC flag
	analog_selected = 0; // Select analog channel

	// Set port

	ADMUX &= ~(1 << MUX2);
	ADMUX &= ~(1 << MUX1);
	ADMUX &= ~(1 << MUX0);

	ADCSRA |= (1 << ADSC); // Start ADC
}

// Get right IR
void get_ir_right()
{
	adc_flag = 1;		 // Set ADC flag
	analog_selected = 1; // Select analog channel

	// Set port

	ADMUX &= ~(1 << MUX2);
	ADMUX |= (1 << MUX1);
	ADMUX &= ~(1 << MUX0);

	ADCSRA |= (1 << ADSC); // Start ADC
}

void get_gyro()
{
	adc_flag = 1;
	analog_selected = 2;

	// Set port

	ADMUX |= (1 << MUX2);
	ADMUX &= ~(1 << MUX1);
	ADMUX &= ~(1 << MUX0);

	ADCSRA |= (1 << ADSC); // Start ADC
}

// Get right IR
void get_ir_front()
{
	adc_flag = 1;		 // Set ADC flag
	analog_selected = 3; // Select analog channel

	// Set port
	ADMUX |= (1 << MUX2);
	ADMUX |= (1 << MUX1);
	ADMUX &= ~(1 << MUX0);

	ADCSRA |= (1 << ADSC); // Start ADC
}

void get_odometer()
{
	cli();

	// Need separate to send on TWI
	sensor_data.odometer_h = (uint8_t)(odo_cnt >> 8);
	sensor_data.odometer_l = (uint8_t)(odo_cnt & 0xFF);

	sei();
}

int main(void)
{

	analog_selected = 0;
	adc_flag = 0;
	sensor_data.automatic_drive = 1;
	sensor_data.start_drive = 1;
	odo_cnt = 0;

	init_ddr();
	init_adc();
	init_twi();
	init_interrupts();

	while (1)
	{

		get_ir_left();
		while (adc_flag == 1)
			; // Busy waiting for ADC

		get_ir_right();
		while (adc_flag == 1)
			; // Busy waiting for ADC

		get_gyro();
		while (adc_flag == 1)
			; // Busy waiting for ADC

		get_ir_front();
		while (adc_flag == 1)
			;

		get_odometer();
	}
	return 0;
}

// External interrupt INT0 ISR
ISR(INT0_vect)
{
	cli();

	if (sensor_data.automatic_drive == 0)
	{
		sensor_data.automatic_drive = 1;
	}
	else
	{
		sensor_data.automatic_drive = 0;
	}

	sei();
}

// Interrupt for odometer
ISR(INT1_vect)
{
	cli();

	_delay_ms(1); // Not debounced and therefore delay is needed

	if (PIND & (1 << PIND3))
	{ // Check if signal still high after 1 ms
		odo_cnt++;
	}

	sei();
}

ISR(INT2_vect)
{
	cli();

	if (sensor_data.start_drive == 0)
	{
		sensor_data.start_drive = 1;
	}
	else
	{
		sensor_data.start_drive = 0;
	}

	sei();
}

// ADC conversion complete ISR
ISR(ADC_vect)
{
	cli();

	// Save the high bits of ADC to selected channel and remove flag
	switch (analog_selected)
	{
	case 0:
		sensor_data.ir_left = ADCH;
		adc_flag = 0;
		break;
	case 1:
		sensor_data.ir_right = ADCH;
		adc_flag = 0;
		break;
	case 2:
		sensor_data.gyro = ADCH;
		adc_flag = 0;
		break;
	case 3:
		sensor_data.ir_front = ADCH;
		adc_flag = 0;
		break;
	default:
		asm("nop");
		sei();
	}
}

ISR(TWI_vect)
{

	uint8_t status = TWSR;

	switch (status & 0xF8)
	{

	// Slave transmitter
	case 0xA8: // Own address received

		// Load data to data register
		switch (chosen_data)
		{
		case 0:
			twi_data = sensor_data.automatic_drive;
			break;
		case 1:
			twi_data = sensor_data.ir_front;
			break;
		case 2:
			twi_data = sensor_data.ir_left;
			break;
		case 3:
			twi_data = sensor_data.ir_right;
			break;
		case 4:
			twi_data = sensor_data.odometer_h;
			break;
		case 5:
			twi_data = sensor_data.odometer_l;
			break;
		case 6:
			twi_data = sensor_data.gyro;
			break;
		case 7:
			twi_data = sensor_data.start_drive;
			break;
		default:
			twi_data = -1;
			break;
		}

		TWDR = twi_data;

		TWCR |= (1 << TWINT) | (1 << TWEA);

		break;
	case 0xB8: // Data byte sent, ACK received
		TWCR |= (1 << TWINT);
		break;

	case 0xC0: // Last byte sent and NACK received
		TWCR |= (1 << TWINT) | (1 << TWEA);
		break;

	case 0xC8: // Last byte sent and ACK received
		TWCR |= (1 << TWINT);
		break;

	// Slave receiver
	case 0x60: // Address called, send ACK
		TWCR |= (1 << TWINT) | (1 << TWEA);
		break;

	// Data has been received
	case 0x80: // Address called in prev call, ack sent. Data received.
		chosen_data = TWDR;

		TWCR |= (1 << TWINT) | (1 << TWEA);
		break;

	// Stop condition
	case 0xA0:
		TWCR |= (1 << TWINT) | (1 << TWEA);
		break;

	// Other
	default: // Unknown error: reset TWI interface
		TWCR |= (1 << TWSTO) | (1 << TWINT) | (1 << TWEA);
		break;
	}
}
