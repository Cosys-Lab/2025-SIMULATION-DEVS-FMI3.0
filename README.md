# 2025-SIMULATION-DEVS-FMI3.0

This repository contains all the code required to reproduce the results of the paper **"Adapting Parallel DEVS Semantics to FMI 3.0 Co-Simulation Using Synchronous Clocks"** (*SIMULATION*, 2025, doi: <https://doi.org/10.1177/00375497251393255>).

## 📌 Steps to Reproduce

1. **Clone this repository**:
    ```sh
    git clone https://github.com/Cosys-Lab/2025-SIMULATION-DEVS-FMI3.0.git
    cd 2025-SIMULATION-DEVS-FMI3.0
    ```

2. **Ensure Google Protobuf is Updated**  
   *The UniFMU backends run with the system's default Python interpreter, ignoring the virtual environment (venv).  
   The Protobuf messages were compiled with version **5.27.3**, so the runtime version must be at least **5.27.3**.*
    ```sh
    pip install "protobuf>=5.27.3"
    ```

2. **Create a Python virtual environment**:
    ```sh
    python -m venv venv
    ```

3. **Activate the virtual environment**:
    - **Windows**:
        ```sh
        venv\Scripts\activate
        ```
    - **Linux/macOS**:
        ```sh
        source venv/bin/activate
        ```

4. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

5. **Run the script to reproduce results**:
    ```sh
    python run_reproduction_simulation_2025.py
    ```

---

## 📖 How to Cite

Paper doi: <https://doi.org/10.1177/00375497251393255>

If you use this code in your research, please cite:

```bibtex
@article{vanommeslaeghe2025adapting,
  title={Adapting parallel DEVS semantics to FMI 3.0 co-simulation using synchronous clocks},
  author={Vanommeslaeghe, Yon and Gomes, Claudio and Van Acker, Bert and Denil, Joachim and De Meulenaere, Paul},
  journal={SIMULATION},
  pages={00375497251393255},
  year={2025},
  publisher={SAGE Publications Sage UK: London, England},
  doi={10.1177/00375497251393255}
}
```

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0**.  
See [`LICENSE`](LICENSE) for details.

### Third-Party Licenses
This repository includes third-party components that are licensed under separate terms:

- **PythonPDEVS (v2.4.2)**  
  - Licensed under the **Apache License 2.0**.  
  - See [`pypdevs/LICENSE`](pypdevs/LICENSE) for details.
  - Original repository: https://msdl.uantwerpen.be/git/yentl/PythonPDEVS

- **UniFMU (from INTO-CPS)**  
  - Licensed under the **INTO-CPS Association Public License (ICAPL)**.  
  - See [`ICAPL_LICENSE`](ICAPL_LICENSE) for details.
  - Original repository: https://github.com/INTO-CPS-Association/unifmu

By using this software, you agree to comply with **all included license terms**.
