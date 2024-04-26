/*
 * main.h
 *
 * Created: 2023-11-02 16:40:10
 *  Author: chrna581
 */ 

#ifndef _main_h
#define _main_h

#include <stdint.h>

#define DEFAULT_SPEED 100
#define DEFAULT_ROTATE_SPEED 100
#define MAX_SPEED 255
#define MIN_SPEED 0

void setup_pmw_timer();
void set_speed(uint8_t input_data);
void set_right_speed(uint8_t speed);
void set_left_speed(uint8_t speed);
void set_left_direction(uint8_t dir);
void set_right_direction(uint8_t dir);
void set_direction(bool dir);
void set_directives(uint8_t speed);

#endif
