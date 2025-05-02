# **Interactive Platform for Automated RF Testing with VNA and FPGA Devices**

# **1\. Installation**

## **1.1 Python**

	Install any version of Python between versions  3.9 to 3.13 from the link below.   
[https://www.python.org/downloads/](https://www.python.org/downloads/)  
Make sure that Python is included in the PATH when installing. This can be tested by opening the Command Prompt and entering “python \--version”. If it shows an error, it means that Python is not added to the PATH. In that case follow the tutorial in the below link to do so:  
[https://realpython.com/add-python-to-path/](https://realpython.com/add-python-to-path/)  
	The following python libraries are required to run the application:

* Tkinter  
* PyVisa  
* pySerial

	They can be installed by running the following command in your terminal:

| pip install tk pyvisa pyserial |
| :---- |

Make sure the serial module is not installed as it might interfere with the functioning of the pyserial module by running the following command:

|  pip uninstall serial |
| :---- |

## **1.2 VISA**

	VISA, which stands for “Virtual Instrument Software Architecture”, is an API (Application Programming Interface) used for controlling and communicating with test and measurement instruments such as VNAs. As this application is made and tested with a Rohde & Schwarz VNA, it is recommended to use their VISA from the link below, although even NI-VISA by National Instruments should also be compatible.  
[https://www.rohde-schwarz.com/fi/applications/r-s-visa-application-note\_56280-148812.html](https://www.rohde-schwarz.com/fi/applications/r-s-visa-application-note_56280-148812.html)

# **2\. API Reference**

	The backend for this application is split into 2 parts: fpga.py and vna.py.

## **2.1. FPGA.py**

### **class FPGA**

	This class provides an interface to communicate with an FPGA device over UART (serial). It handles device discovery and allows triggering states via a serial connection.

| Attribute | Type | Description |
| ----- | ----- | ----- |
| connected | bool | True if FPGA is discovered. False if not |
| port | str or None | Stores the port that the FPGA is connected to |
| baudrate | int | Communication speed with the UART. Default is 9600 |
| timeout | int | Timeout for operations in seconds. Default is 1 |

**Example**:

| fpga \= FPGA(baudrate=9600, timeout=1) |
| :---- |

### **initialize\_fpga()**

	Scans available serial ports for a device containing `"USB Serial"` in its description. Automatically sets the port and marks the FPGA as connected.

**Example**:

| status \= fpga.initialize\_fpga() |
| :---- |

**Returns**:

* **True** if the FPGA is found and initialized.  
* **False** if FPGA is not found.

### **trigger\_state(state)**

	Sends a one-byte command to the FPGA to trigger a digital input state. Reads and prints the response if available.

**Example**:

| success \= fpga.trigger\_state(5) |
| :---- |

**Parameters**:

* **state (int):** An integer representing the state that needs to be triggered

**Returns**:

* **True** if the state is triggered.  
* **False** if there is an error while triggering state.

## **2.2 VNA.py**

### **class VNA**

	A class to interact with a Vector Network Analyzer (VNA), specifically models from Rohde & Schwarz. Provides functionality to connect to the device, retrieve trace information, and save amplitude or full trace data.

| Attribute | Type | Description |
| ----- | ----- | ----- |
| connected | bool | Flag indicating whether VNA is connected or not |
| instru | pyvisa.Resource | VISA instrument resource object representing the connected VNA |
| start\_index | int | Starting index of frequency range to extract. |
| start\_index | int  | Ending index of frequency range to extract. |
| sep | str | Seperator for the output CSV |

**Example**:

| van  \= VNA() |
| :---- |

### **initialize\_vna():**

Attempts to locate and connect to a Rohde & Schwarz VNA using the PyVISA resource manager. 

**Example**:

| status \= vna.initialize\_vna() |
| :---- |

**Returns**

* **True** if the VNA is found and connected.  
* **False** if no VNA is found.

### **get\_trace\_info(start\_freq, stop\_freq)**

	Fetches frequency points and trace metadata from the VNA and formats filenames accordingly.

**Example**:

| freqs, trace\_names \= vna.get\_trace\_info(start\_freq=15.5, stop\_freq=17.5) |
| :---- |

Parameters:

* **start\_freq (float, optional)**: Custom start frequency in GHz.  
* **stop\_freq (float, optional)**: Custom stop frequency in GHz.

Returns

* **Tuple** containing  
  * **List\[float\]** containing frequency points  
  * **List\[str\]** containing formatted CSV trace file names.

### **save\_traces\_amp(folder\_name, start\_freq, end\_freq)**

Saves trace data collected when testing amplifiers  in a given frequency range to individual CSV files.

**Example**:

| vna.save\_traces\_amp("data\_folder", start\_freq=15.5, end\_freq=17.5) |
| :---- |

**Parameters:**

* **folder\_name (str) :** Path to the folder in which the CSV files needs to be saved  
* **start\_freq (float) :** Start frequency in GHz.  
* **stop\_freq (float) :** Stop Frequency in GHz

### **save\_traces(state, folder\_name, start\_freq, stop\_freq)**

	Saves traces data collected when testing phase shifters in a given frequency range to individual CSV files.

**Example:**

| vna.save\_traces(18, "data\_folder", start\_freq=15.5, end\_freq=17.5) |
| :---- |

**Parameters:**

* **state (int) :** State that has been triggered.  
* **folder\_name (str) :** Path to the folder in which the CSV files needs to be saved  
* **start\_freq (float) :** Start frequency in GHz.  
* **stop\_freq (float) :** Stop Frequency in GHz

### **reset\_indices()**

	Resets the cached frequency indices so that they can be recalculated during a new save operation.

**Example:**

| vna.reset\_indices() |
| :---- |

