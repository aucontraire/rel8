<img src="https://github.com/aucontraire/rel8/blob/master/rel8/static/images/rel8-logo.png" alt="rel8 logo" width="450"/>

# rel8

## Description

This project allows you to test hypotheses about the relationship of two variables using SMS based on their shared frequency. A common use case is health symptoms that you may suspect are being caused by something.

---

## Environment

* __OS:__ Ubuntu 14.04 LTS
* __language:__ Python 3.4.3
* __application server:__ Flask 1.0, Jinja2 2.9.6
* __database:__ MySQL Ver 14.14 Distrib 5.7.18

<img src="https://github.com/jarehec/AirBnB_clone_v3/blob/master/dev/hbnb_step5.png" />


## Setup

This project comes with various setup scripts to support automation, especially
during maintanence or to scale the entire project.  The following files are the
setupfiles along with a brief explanation:

* **`Enrollment`:** Initial enrollment happens when you text to the assigned Twilio number where you will be asked if you want to sign up as well as being asked your name. A link will be generated with an access code that will redirect you to the website

  * Access code: `The access code needs to match the number it was paired with and doesn't have an expiration date.`

* **`Registration`:** Once at the website you will be prompted to choose a password so that you can complete the registration

  * Password: `The password needs to be at least 8 characters long`

* **`Variables set up`:** In this form you will set up the predictor and outcome variables as well as a session duration. The words that you choose are the same words that the system will expect you to text to match them up with the right variables. 

  * Session: `The session duration determines how long you want to wait in hours before a predictor variable cannot be paired with an outcome variable. The session duration cannot be less than one hour.`

* **`Data collection phase`:** Once you've completed the steps above you are ready to collect data. Begin texting the variable words that you picked.

  * Errors: `If you sent a word that is not linked to one of your variables, you will get an text telling you it is an error. This data will not be saved. If you text a predictor when an outcome is expected (e.g., when a session is still open), you will also get an error message.`


## Authors

* [aucontraire](https://github.com/aucontraire)

## License

MIT License
