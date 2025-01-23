# EyeSpy

***
<p style="font-size: large">
  A lightweight application aiming to automate the process of measuring the fluorescence of a fly's eye. Designed to be used alongside ZEN Microscopy Software.
</p>


## Features

  - Calculation of the mean flourescence of a fly's eye over a circular region of interest (ROI).
  - Automatic detection and processing of images being taken by microscopy software.
  - Automatic detection of circular ROIs less than or equal to a specified radius in micrometers (2500 μm by default).
  - Designed for use with .czi files, with support for .tiff files.
  - Lightweight image processing.
  - Data is automatically written into a .csv file.
  - Customizable output.


## Installation and Configuration

  Download and extract EyeSpy.zip into a folder.
  
  To run the program, execute EyeSpy.exe.
  
  On first launch, you will be prompted with a file explorer popup. Select the folder where your microscopy software temporarily saves images after they are captured. This setting can be changed in the options.ini file at any time.

  By default, EyeSpy is configured to  process .czi files. You can process .tiff files by changing the "filetype" option in the options.ini file.
  
   ⚠️ **IMPORTANT: When using .tiff files, you must MANUALLY SET your scaling! Change the "scaling" option in options.ini to the numeric value of your images' scaling, in micrometers/pixel!** ⚠️

  Ensure that your exposure time is set correctly. This prevents the program from accessing images before they are completely written, which will throw an error (Default: 1000 ms).
  
  Other settings are relatively straightforward to configure.

## File Requirements

  - Supported Filetypes: .czi, .tiff
  - Images should be one-channel (grayscale)
  - Image data should be primarily contained within two dimensions (no support for Z-Stack imaging)
  - Images should reasonably depict the fly's eye; avoid fluorescence from external light sources, foreign objects covering the eye, or images depicting unreasonably small regions of the eye.

## Running the Program

  Upon pressing "Start", a blank window with a textbox will appear. 
  
  ![image](https://github.com/user-attachments/assets/24783562-7b0c-43fe-893d-ec0289447aa7)

  This textbox will display the mean fluorescence values for each image captured, and will be updated immediately after image processing is completed. Concurrently, output values will be written in a .csv file, labelled with the current date and time.
  
  Errors will also be shown within the textbox.

  While images are being processed, the program may appear unresponsive. Ideally, avoid interacting with the window while it is processing data.

  To stop a processing session, simply exit the open window.


## The Pipeline

🚧 **This section is currently under construction as the pipeline is being refined for the first stable release.** 🚧

1) Images are retrieved from the specified directory, a set time after they are first detected (to avoid opening files before they are completely written)

2) For .czi images, metadata is unpacked to retrieve scaling data.

3) The image is opened as a two-dimensional matrix of values, where the fluorescence *F* of a pixel can be expressed as a function of its location *(x,y)*.

   ![image](https://github.com/user-attachments/assets/e8e58c2a-a36a-4d50-962a-817b508617df)

   Given that the images being processed are single-channel, we assume that variance in *f(x,y)* is caused by variation in fluorescence.
   
4) Each value in the two-dimensional matrix is normalized by

   ![image](https://github.com/user-attachments/assets/cdcecb8b-815c-426f-8157-15062de18dc0)

   where *f '(x,y)* is the new value of the pixel at location *(x,y)*, *max{f(x,y)}* is the largest value in the original matrix excluding outliers, and 255 is a constant representing the white point of an image.

   This process effectively allows us to redefine the value of each pixel in the image proportionately to the brightest value in the image, which facilitates the processing of darker images down the line. As a trade-off, this technique can sometimes draw out fluorescence in the background, which is handled in later steps.

   ![image](https://github.com/user-attachments/assets/1c897a1a-cd95-400e-8843-7b57fe3f90c8)

5) To facilitate further processing, the image is converted into a binary image using thresholding.

   This process is under heavy revision as we conduct tests to determine the most accurate way to threshold varying images.
   
   ![image](https://github.com/user-attachments/assets/f875b4f9-4bb3-4dae-ac5f-ebc0d7ff48cd)

6) Leveraging the OpenCV library, the distance transform is applied to the thresholded image in order to eliminate potential fluoresence originating from the fly's body.

   ![image](https://github.com/user-attachments/assets/666f0f95-0b3a-44e7-8264-f3fc1e12694c)

7) Once again with the OpenCV library, contour detection is utilized to separate the eye (the largest contour) from any potential background fluorescence slipping through thresholding.

   ![image](https://github.com/user-attachments/assets/666f0f95-0b3a-44e7-8264-f3fc1e12694c)

8) Using OpenCV, an ellipse is roughly fitted to the region marked as the eye to determine the approxite boundaries and radius of the eye.

   ![image](https://github.com/user-attachments/assets/666f0f95-0b3a-44e7-8264-f3fc1e12694c)

9) Data from the previous step is used to determine a circular region of interest contained entirely within the fly's eye.

    ![image](https://github.com/user-attachments/assets/fb45c356-ec71-4f33-9dc7-1e864db145f1)

    Let R be the set of pixels contained within the circular region of interest.

   ![image](https://github.com/user-attachments/assets/666f0f95-0b3a-44e7-8264-f3fc1e12694c)

10) Finally, the mean fluorescence value of the circular region of interest is calculated:

    ![image](https://github.com/user-attachments/assets/146f5696-f098-4aa7-94e3-623fc6b4a9ca)

    ![image](https://github.com/user-attachments/assets/666f0f95-0b3a-44e7-8264-f3fc1e12694c)
   


## To Do
  
  - Add user interface for configuring settings.
  - Refactor GUI code.
  - Ensure portability (macOS, Linux).
  - Add the capability to calculate fluorescence of existing images in a directory, rather than only in a live environment.
  - Add images to README
