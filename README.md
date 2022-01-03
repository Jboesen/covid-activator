# Automatic Color COVID Test Activator

Harvard affiliates have to take Color's COVID tests. You have to sign in, go to the same website, and check the same boxes week after week. It almost seems like a computer could do it for you... 

Of course a computer could do it for you. With this website, you can scan the C-... and D-... numbers on the blue sheet of paper that comes with a test, and the computer does the rest. 

To use it, go to https://covid-activator.herokuapp.com/register to create an account. Creating an account stores your Color login information, but your password is encrypted with a client-side key. Once you create your account, you can log in. You will be automatically redirected to the login page after you register or whenever you try to access the site without logging in. Log in, and you will be directed to the "text recognition" page. This is where you can upload a photo of the codes, and the computer will pass the numbers. A filename might not show up, but the file is uploaded. Click submit, double-check your codes, click submit again, and the program will submit the codes to Color. If you prefer to manually enter your codes, you can click or tap "manual" and "text recognition" to toggle input methods. On the manual page, you can input your codes and submit them. In either case, (and as the page clearly states) only use this if you don't have any symptoms and none of your information has changed. If these methods work, you will be redirected to a page saying "Kit activated successfully!". Otherwise, you will get an error or be redirected to "Something went wrong."

Because this uses Selenium, you cannot execute this on your machine unless you adjust the code to specify where to find a chromedriver and Google Chrome. It only works on the linked website, which has a Chromedriver built-in. 

If you forget your password, go to the login page, click "Delete Account," and follow the instructions. 
