This project develops and improves on PyTesser, which can be found here:  https://pypi.python.org/pypi/PyTesser/ 
 
## Inspiration 
While fiddling with reverse engineering the Tinder API, I thought it would be cool to make Tinder accounts dynamically.  To do that, one must be able to make Facebook accounts dynamically.  To make Facebook accounts dynamically, you must make email accounts dynamically. 
 
So, I decided to write a script that would generate Gmail accounts dynamically.  This was simple, but required solving captchas. 
 
## About CaptchaSolver 
CaptchaSolver was created to solve Gmail captchas specifically. 
Gmail captchas come in two forms:  Street names, and building numbers.  CaptchaSolver solves building number captchas only. 
 
## Method 
PyTesser can be used to interpret an image of well-formed text (like the text you are reading).  Captchas are obviously not well formed.  Therefore, a number of mutations (ie. changing in contrast, cascading, tilting, etc.) are applied to the input image.  After each mutation, PyTesser is used to interpret the text.  Most of the interpretations will be no good due to image noise.  These noisy interpretations will have seemingly random names.  The correct interpretations will have identical names.  Therefore, even though the number of correct interpretations will be few, the number of appearances of the correct name will exceed those of all others (in most cases). 
 
## Input & Preparation & Outputs 
- 1)  Have your desired image named "image.jpg" 
- 2)  python captchaSolver.py 
- 3)  The final output marked prediction will be False if no confident guess could be made.  Otherwise, it will be the numerical value of the captcha. 
 
## Other 
The folder "Images" has some sample images
