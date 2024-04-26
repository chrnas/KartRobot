/**
 * styrmodul.c
 *
 * Created: 2023-10-31 09:46:01
 * Author : G07
 * Modifications:
 * Description: Controls the Sumo(Terminator) based on a 8 bit input from Raspberry Pie 4.0.
 */

#include <avr/io.h>
#include <stdbool.h>
#include <avr/interrupt.h>
#include <stdio.h>
#include "main.h"

volatile uint8_t left_speed = 0;
volatile uint8_t right_speed = 0;
volatile uint8_t right_dir = 0;
volatile uint8_t left_dir = 0;
volatile uint8_t left_right_bit = 0;
volatile uint8_t speed = 0;
volatile uint8_t forward_backward_bit = 0;
volatile uint8_t movement_input = 0x00; // 8-bit input from Raspberry pie.

/**
 * @brief Main function
 */
int main(void)
{
	// Configure data direction registers for ports A, D, and C
	DDRA = 0x05;
	DDRD = 0x30;
	DDRC = 0x00;

	// Initialize port values for motors and TWI
	PORTD = (0 << PORTD4 | 0 << PORTD5);
	PORTA = (1 << PORTA0 | 1 << PORTA2);
	PINC = (0 << PINC0 | 0 << PINC1);

	setup_pmw_timer();
	set_speed(movement_input);

	// Set up TWI
	TWAR = 254; // Set Slave address
	TWCR = (1 << TWEA) | (1 << TWEN) | (1 << TWIE);
	sei(); // Enable global interrupts
	while (1)
	{
		asm("nop");
	}
}

/**
 * @brief Function to set motor speeds and direction.
 * @param input_data: 8-bit input to set speed and direction of motors. Bit 7 Right direction, bit 6-4 Right speed, bit 3 left direction, bit 2-0 left speed.
 */
void set_speed(uint8_t input_data)
{
	cli(); // Disable global interrupts during critical section

	// Extract direction and speed for motors from input
	// right_dir = (input_data & 0x80) >> 7;
	left_right_bit = (input_data & 0x80) >> 7;		 // 0=L,R=1
	forward_backward_bit = (input_data & 0x40) >> 6; // 0=B, 1=F
	speed = (input_data & 0x3F) * 4;

	// xxxxxx * 4
	// left_dir = (input_data & 0x08) >> 3;
	// right_speed = (input_data & 0x70)  << 1;
	// left_speed = (input_data & 0x07) << 5;

	if (left_right_bit == 0)
	{
		set_left_speed(speed);
		set_left_direction(forward_backward_bit);
	}
	else
	{
		set_right_speed(speed);
		set_right_direction(forward_backward_bit);
	}
	/*
	if(right_speed != 0) {
		right_speed = right_speed - 12 * ((right_speed >> 5) - 3);
	}
	if(left_speed != 0) {
		left_speed = left_speed - 12 * ((left_speed >> 5) - 3);
	}

	//Set direction and speed for motors
	set_right_direction(right_dir);
	set_left_direction(left_dir);
	set_right_speed(right_speed);
	set_left_speed(left_speed);

	*/
	sei(); // Enable global interrupts
}

void setup_pmw_timer()
{
	// Configure Timer/Counter 1 for PWM
	TCCR1B = (0 << WGM31) | (1 << WGM21) | (0 << CS12) | (0 << CS11) | (1 << CS10);
	TCCR1A = (0 << COM1A0) | (1 << COM1A1) | (0 << COM1B0) | (1 << COM1B1) | (0 << WGM11) | (1 << WGM10);
	cli();					// Disable global interrupts during configuration
	TIMSK1 = (1 << OCIE1A); // Enable Timer1 Output Compare Match Interrupt(TWI interrupt) is enabled.
	sei();					// Enable global interrupts
}

void set_right_speed(uint8_t speed)
{
	OCR1A = speed; // OCR1A - Velocity of Right wheel: Still = 0 - Max speed = 255
}

void set_left_speed(uint8_t speed)
{
	OCR1B = speed; // OCR1A - Velocity of Left wheel: Still = 0 - Max speed = 255
}

void set_right_direction(uint8_t dir)
{
	PORTA &= 0b11111011;
	PORTA |= ((uint8_t)dir << PORTA2); // dir = 1 -> forward, dir = 0 -> backward
}

void set_left_direction(uint8_t dir)
{
	PORTA &= 0b11111110;
	PORTA |= ((uint8_t)dir << PORTA0); // dir = true = 1 -> forward, dir = false = 0 -> backward
}

/**
 *	@brief Interrupt Service Routine for TWI
 */
ISR(TWI_vect)
{
	uint8_t status = TWSR; // Read status register to determine the current state
	switch (status)
	{
	case 0x60:
		TWCR |= (1 << TWINT) | (1 << TWEA);
		break;
	case 0x68:
		TWCR |= (1 << TWINT) | (1 << TWEA);
		break;
	case 0x70:
		TWCR |= (1 << TWINT) | (1 << TWEA);
		break;
	case 0x80:
		movement_input = TWDR;
		TWCR |= (1 << TWINT) | (1 << TWEA);
		set_speed(movement_input);
		break;
	case 0x88:
		TWCR |= (1 << TWINT) | (1 << TWEA);
		break;
	case 0x90:
		TWCR |= (1 << TWINT) | (1 << TWEA);
		break;
	case 0x98:
		TWCR |= (1 << TWINT) | (1 << TWEA);
		break;
	case 0xA0:
		TWCR |= (1 << TWINT) | (1 << TWEA);
		break;
	default:
		// Print error status if unknown state is encountered
		printf("error : %02x", status);
	}
}

ISR(TIMER1_COMPA_vect)
{
}
