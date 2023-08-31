# MFA + OpenAI/ElevenLabs Proxy

<a name="readme-top"></a>

[![MIT License][license-shield]][license-url]

## 🤔 What is this?
This project was created for LabLab.ai's ElevenLabs hackathon. [Project Video](https://lablab.ai/event/eleven-labs-ai-hackathon/phomemes/languagelearner)

A local server proxy for OpenAI/ElevenLabs services and for Montreal Forced Alignment.

Used in development with [LanguageLearner](https://kael558.github.io/LanguageLearner/)

## 🔧 Installation
`pip install -r requirements.txt`

Install Montreal Forced Aligner [here](https://montreal-forced-aligner.readthedocs.io/en/latest/getting_started.html):

Activate the environment:
`conda activate aligner`

Download the english_us_arpa acoustic model and dictionary:
`mfa model download acoustic english_us_arpa`
`mfa model download dictionary english_us_arpa`

Run the flask app with:
`flask --app main run`

You are good to go.

## ⚖️ License
Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

[license-shield]: https://img.shields.io/badge/License-MIT-yellow.svg
[license-url]: https://github.com/kael558/LanguageLearner/blob/main/LICENSE
