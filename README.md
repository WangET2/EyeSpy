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

   The domain of the function spans the set of valid pixel locations of the image *I*.

   ![image](https://github.com/user-attachments/assets/e289aba8-954d-49df-a102-840aabb78530)

   Given that the images being processed are single-channel, we assume that variance in *f(x,y)* is caused by variation in fluorescence.
   
4) Each value in the two-dimensional matrix is normalized by

   ![image](https://github.com/user-attachments/assets/cdcecb8b-815c-426f-8157-15062de18dc0)

   where *f '(x,y)* is the new value of the pixel at location *(x,y)*, *max{f(x,y)}* is the largest value in the original matrix excluding outliers, and 255 is a constant representing the white point of an image.

   This process effectively allows us to redefine the value of each pixel in the image proportionately to the brightest value in the image, which facilitates the processing of darker images down the line. As a trade-off, this technique can sometimes draw out fluorescence in the background, which is handled in later steps.

   ![Figure_1](https://github.com/user-attachments/assets/2965659c-8974-4f6d-a62d-90051faab85e)


5) To facilitate further processing, the image is converted into a binary image using thresholding.

   This process is under heavy revision as we conduct tests to determine the most accurate way to threshold varying images.
   
   ![Figure_2](https://github.com/user-attachments/assets/78f3de2d-cd65-4d4b-9ae7-e8b222b3c0e9)


6) Leveraging the OpenCV library, the distance transform is applied to the thresholded image in order to eliminate potential fluoresence originating from the fly's body.

   ![Figure_3](https://github.com/user-attachments/assets/e95126af-9c3d-41d4-a869-b0818295b853)


7) Thresholding is applied again in order to eliminate connection points between the fly's eye and body.

   ![Figure_4](https://github.com/user-attachments/assets/249b1169-96eb-4668-b757-31336b9a85a9)


8) Once again with the OpenCV library, contour detection is utilized to separate the eye (the largest contour) from any potential background fluorescence slipping through thresholding.

   ![Figure_5](https://github.com/user-attachments/assets/c5d31160-566c-4be9-a1df-bd27df4dc2f2)


9) Using OpenCV, an ellipse is roughly fitted to the region marked as the eye to determine the approxite boundaries and radius of the eye.

   ![Figure_6](https://github.com/user-attachments/assets/a0504683-fab0-45e0-8020-0b4561a9e92d)


10) Data from the previous step is used to determine a circular region of interest contained entirely within the fly's eye.

    ![Figure_7](https://github.com/user-attachments/assets/9c93537c-9933-4706-87f3-e8d515d4fcdc)

    Let *P* be the set of pixels contained within the circular region of interest, *I* be the set of pixel locations in the image, *(x<sub>c</sub>, y<sub>c</sub>)* be the coordinates of the pixel identified as the center of the eye, and *r* be the radius of the ROI.

    ![image](https://github.com/user-attachments/assets/a28b009a-4222-46f8-9fdb-86b745cd873a)


11) Finally, the mean fluorescence value of the circular region of interest is calculated:

    ![image](https://github.com/user-attachments/assets/67912d6c-cc81-489e-aee9-881707cee151)

    ![image](https://github.com/user-attachments/assets/18988f4b-c9d0-4c57-9405-765691d08da6)

   


## To Do
  
  - Add user interface for configuring settings.
  - Refactor GUI code.
  - Ensure portability (macOS, Linux).
  - Add the capability to calculate fluorescence of existing images in a directory, rather than only in a live environment.
  - Add images to README
