import os
import base64
from ndn.security import KeychainSqlite3, TpmFile


def create_keys(path="sec_data/", entities=["worker", "driver"], app_prefix='ndn-compute'):
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, 'certs'), exist_ok=True)

    for entity in entities:
        os.makedirs(os.path.join(path, entity), exist_ok=True)

        keychain_path = os.path.join(path, entity, 'pib.db')
        tpm_path = os.path.join(path, entity, 'ndnsec-key-file')
        tpm = TpmFile(tpm_path)
        success = KeychainSqlite3.initialize(keychain_path, 'tpm-file', tpm_path)

        if not success:
            raise Exception(f"Could not make keychain and TPM for {entity}")

        keychain = KeychainSqlite3(keychain_path, tpm)

        identity = keychain.touch_identity(f'/{app_prefix}/{entity}')
        keychain.set_default_identity(identity.name)

        self_signed_cert = bytes(identity.default_key().default_cert().data)

        cert_path = os.path.join(path, 'certs', f'{entity}.base64')
        with open(cert_path, 'w') as file:
            file.write(base64.b64encode(self_signed_cert).decode('utf-8'))
