Beskrivet på sida 228 i manual https://ww1.microchip.com/downloads/en/DeviceDoc/doc8059.pdf

sätt TWAR till slavens adress. (TWGCE=1 gör så att den även lyssnar på general call adress (0x00), så sätt till 0)

I TWCR: (1 << TWEA) | (1 << TWEN)

Nu väntar slaven på att få sin adress.

När adress kommer sätts TWINT (Init) blir 1 och status kan läsas från TWSR (Status register)


``` C
#define SLAVE_ADDRESS 0x20 // 7-bit I2C slave address

volatile uint8_t dataToSend = 0; // Data to be transmitted

// TWI Slave Transmitter mode interrupt service routine
ISR(TWI_vect) {
    switch (TWSR & 0xF8) {
        // Slave Transmitter mode


        case 0xA8: //Address has been received
            // Load data to the data register for transmission
            TWDR = dataToSend;

            // Clear the TWI interrupt flag and enable ACK
            TWCR = (1 << TWINT) | (1 << TWEA);
            break;

        case 0xB8: //Databyte sent, ACK received


            TWDR = dataToSend;

            if(more_than_1_byte_left) {

              // Clear the TWI interrupt flag and enable ACK
              TWCR = (1 << TWINT) | (1 << TWEA);
            } else { //last byte
              // NACK expected
              TWCR = (1 << TWINT);

            }


            break;




        case 0xC0: //Last byte sent and NACK received
            // Disable TWI, and release the SDA line
            TWCR = (1 << TWINT);
            break;

        case 0xC8: //Last byte sent and ACK received
            // Disable TWI, and release the SDA line
            TWCR = (1 << TWINT);
            break;

        default:
            // Unknown error; reset the TWI interface
            TWCR = (1 << TWSTO) | (1 << TWINT) | (1 << TWEA);
            break;
    }
}

int main(void) {
    // Set the TWI slave address (last bit as zero)
    TWAR = (SLAVE_ADDRESS << 1);

    // Enable the TWI interface, generate acknowledge on data received
    TWCR = (1 << TWEN) | (1 << TWEA);

}

```
