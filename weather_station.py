#!/usr/bin/python

# Example using a character LCD connected to a Raspberry Pi

import time
import board
from board import *
import Adafruit_DHT
import busio
import digitalio
import adafruit_character_lcd.character_lcd as character_lcd
import adafruit_mcp9808
import RPi.GPIO as GPIO
import numpy as np
import spidev

def startStop(channel):
	global status
	global lcd
	if status == "ON":
		lcd.clear()
		lcd.message = "Stand-by mode"
		GPIO.output(20,GPIO.LOW)
		GPIO.output(26,GPIO.LOW)
		status = "OFF"
		print("Stand-by mode. Press button to start")
	elif status == "OFF":
		status = "ON"
	return status


def initialiseStation(i2c, spi, lcd, LED, count, minute_list):
	global LCD_pages
	moisture_level, LCD_pages = getData(spi, i2c)
	LED_status = LED_status_func(moisture_level)
	lcd.clear()
	lcd.message = LCD_pages[current_page]
	time.sleep(10)
	lcd.clear()


# Read MCP3008 data
def analogInput(channel, spi):
	spi.max_speed_hz = 1350000
	adc = spi.xfer2([1,(8+channel)<<4,0])
	data = ((adc[1]&3) << 8) + adc[2]

	return data


def getData(spi, i2c):
	moisture_level = analogInput(0, spi)
	moisture_level = round((moisture_level/1023*100), 1)
	moisture_string = ("Moisture: " + str(moisture_level) + "%")

	t = adafruit_mcp9808.MCP9808(i2c)
	temp = round(t.temperature, 1)
	temp_string = "Temp: " + str(temp) + chr(223) + "C"

	humidity, AdaFruitTemp = Adafruit_DHT.read_retry(11, 4)
	humidity_string = "Humidity: " + str(round(humidity, 1)) + "% RH"

	LCD_line_1 = moisture_string + "\n" + temp_string
	LCD_line_2 = humidity_string

# 	print(LCD_line_1 + "\n" + LCD_line_2)
	global LCD_pages
	LCD_pages = [LCD_line_1, LCD_line_2]

	time_stamp = time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime())
	curr_file = open('moisture_level.txt', 'a')
	curr_file.write(time_stamp + "\t" + str(moisture_level) + "\t" + str(temp) + "\t" + str(humidity) + '\n')
	curr_file.close()

	return moisture_level, LCD_pages


def LED_status_func(moisture_level):
	if moisture_level > 50:
		GPIO.output(20,GPIO.LOW)
		GPIO.output(26,GPIO.HIGH)
		LED_status = GPIO.output(26,GPIO.HIGH)
	else:
		GPIO.output(26,GPIO.LOW)
		GPIO.output(20,GPIO.HIGH)
		LED_status = GPIO.output(20,GPIO.HIGH)
	return


def displayData(channel):
	global current_page
	global lcd
	global status
	global LCD_pages
	if status == "ON":
		if current_page == 0:
			current_page = 1
		elif current_page == 1:
			current_page = 0
		lcd.clear()
		lcd.message = LCD_pages[current_page]
	else:
		pass
	return current_page


def main():
	# Start SPI connection
	spi = spidev.SpiDev()
	spi.open(0,0)

	# Set up Raspberry Pi pins
	GPIO.setwarnings(False)
	GPIO.setup(26,GPIO.OUT)
	GPIO.setup(20,GPIO.OUT)
	GPIO.setup(14,GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
	GPIO.setup(13,GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

	GPIO.output(26,GPIO.LOW)
	GPIO.output(20,GPIO.LOW)

	# Raspberry LCD pin setup
	lcd_rs = digitalio.DigitalInOut(board.D25)
	lcd_en = digitalio.DigitalInOut(board.D24)
	lcd_d7 = digitalio.DigitalInOut(board.D22)
	lcd_d6 = digitalio.DigitalInOut(board.D18)
	lcd_d5 = digitalio.DigitalInOut(board.D17)
	lcd_d4 = digitalio.DigitalInOut(board.D23)

	# Define LCD column and row size for 16x2 LCD.
	lcd_columns = 16
	lcd_rows = 2
	global lcd
	lcd = character_lcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)

	LED = GPIO.output(26,GPIO.LOW)
	GPIO.output(20,GPIO.LOW)
	GPIO.add_event_detect(13,GPIO.RISING,callback=startStop,bouncetime=2000)
	GPIO.add_event_detect(14,GPIO.RISING,callback=displayData,bouncetime=2000)

	global status
	status = "OFF"
	global current_page
	current_page = 0
	count = 0
	minute_list = []
	LCD_pages = []
	print("Stand-by mode. Press button to start")
	while True:
		if status == "ON":
			lcd.clear()
			lcd.message = "Running \nscan"
			with busio.I2C(SCL, SDA) as i2c:
				try:
					initialiseStation(i2c, spi, lcd, LED, count, minute_list)
				except KeyboardInterrupt:
					lcd.clear()
					GPIO.cleanup()
					break
		elif status == "OFF":
			try:
				lcd.message = "Stand-by mode"
				continue
			except KeyboardInterrupt:
				lcd.clear()
				GPIO.cleanup()
				break

main()
