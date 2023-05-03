import os

import requests
from tqdm import tqdm


def ensure_contract(
    filename: str,
    bucket_address: str = "https://storage.googleapis.com/fetch-ai-mainnet-artifacts/",
) -> str:
    base_path = ".contract"
    contract_name = os.path.splitext(filename)[0]
    contract_path = f"{base_path}/{filename}"
    if not os.path.exists(base_path):
        os.mkdir(base_path)
    try:
        temp = open(contract_path, "rb")
        temp.close()
    except OSError:
        response = requests.get(bucket_address + filename, stream=True)
        if response.status_code >= 300:
            raise Exception(f"Contract Download Failed: {contract_name}")
        with open(contract_path, "wb") as contract:
            print(f"\ndownloading {contract_name} contract:")
            for data in tqdm(response.iter_content()):
                contract.write(data)
    return contract_path
