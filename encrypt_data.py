import streamlit as st
from cryptography.fernet import Fernet
import os


# -- Helpers -------------------------------------------------------------


@st.cache_data(show_spinner=False)
def load_key() -> bytes:
    """
    Load the Fernet key from Streamlit secrets.
    """
    # secrets.toml:
    # [cryptography]
    # fernet_key = "..."
    key_str = st.secrets["cryptography"]["fernet_key"]
    return key_str.encode()


def encrypt_file(input_path: str, output_path: str, key: bytes) -> None:
    """
    Encrypt the file at input_path and write to output_path.
    """
    f = Fernet(key)
    with open(input_path, "rb") as f_in:
        data = f_in.read()
    encrypted = f.encrypt(data)
    with open(output_path, "wb") as f_out:
        f_out.write(encrypted)


# -- Streamlit App ------------------------------------------------------

st.title("🔒 Encrypt data.xlsx")

key = load_key()

st.write("**Key loaded from Streamlit secrets.**")

project_dir = os.path.dirname(os.path.abspath(__file__))
data_file_path = os.path.join(project_dir, "data", "data.xlsx")

if not os.path.exists(data_file_path):
    st.error("`data.xlsx` not found in the working directory.")
    st.stop()

if st.button("Encrypt now"):
    output_file_path = os.path.join(
        project_dir, "fixed_deposit_calculator", "data.xlsx.enc"
    )
    try:
        encrypt_file(data_file_path, output_file_path, key)
        st.success(f"✅ Encrypted successfully as `{output_file_path}`")
        st.download_button(
            label="⬇️ Download encrypted file",
            data=open(output_file_path, "rb").read(),
            file_name=output_file_path,
            mime="application/octet-stream",
        )
    except Exception as e:
        st.error(f"Encryption failed: {e}")
