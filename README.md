# open-webui/bot

This repository provides an experimental boilerplate for building bots compatible with the **Open WebUI** "Channels" feature (introduced in version 0.5.0). It serves as a proof of concept to demonstrate bot-building capabilities while highlighting the potential of asynchronous communication enabled by Channels. 

## ⚡ Key Highlights
- **Highly Experimental**: This is an early-stage project showcasing basic bot-building functionality. Expect major API changes in the future.
- **Extensible Framework**: Designed as a foundation for further development, with plans to enhance APIs, developer tooling, and usability.
- **Asynchronous Communication**: Leverages Open WebUI Channels for event-driven workflows.

## 🛠️ Getting Started with Examples
This repository includes an `/examples` folder containing runnable example bots that demonstrate basic functionality. 

To run an example, execute the corresponding module using the `-m` flag in Python. For example, to run the `ai` example:

```bash
python -m examples.ai
```

> **Note**: Ensure that your current working directory (PWD) is the root of this repository when running examples, as this is required for proper execution.

Replace `ai` in the command above with the specific example you’d like to execute from the `/examples` folder.

## 🚧 Disclaimer
This project is an early-stage proof of concept. **APIs will break** and existing functionality may change as Open WebUI evolves to include native bot support. This repository is not production-ready and primarily serves experimental and exploratory purposes.

## 🎯 Future Vision
We aim to introduce improved APIs, enhanced developer tooling, and seamless native support for bots directly within Open WebUI. The ultimate goal is to make building bots easier, faster, and more intuitive.

---
Contributions, feedback, and experimentation are encouraged. Join us in shaping the future of bot-building on Open WebUI!