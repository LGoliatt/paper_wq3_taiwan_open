# -*- coding: utf-8 -*-
"""
Created on Mon Dec 16 13:11:42 2024

@author: Deivid
"""
def read_wq_taiwan(test_size=0.25, seed=42):
    
    from sklearn.model_selection  import train_test_split
    from io                       import BytesIO
    from sklearn.preprocessing    import MinMaxScaler
    
    import numpy      as np
    import pandas     as pd
    import requests

    key = '1a5DReajqstsnUSUdTcRm8pZqeIP9ZmOct834UcOLmjg'
    # Acesso via link
    link = 'https://docs.google.com/spreadsheet/ccc?key=' + key + '&output=csv'
    r    = requests.get(link)
    data = r.content

    # Lendo o CSV com ajustes para evitar warnings
    df = pd.read_csv(BytesIO(data), header=0, low_memory=False)

    # Seleção e transformação de dados
    cols = ['siteid', 'sampledate', 'itemengabbreviation', 'itemvalue']
    data = df[cols]

    # Pivotando os dados
    data = data.pivot(index=['siteid', 'sampledate'], columns='itemengabbreviation', values='itemvalue')

    # Adicionando a coluna 'site'
    data['site'] = [data.index[i][0] for i in range(len(data))]

    # Filtrando os dados
    data = data[data['site'] < 1008]

    # Selecionando as colunas de interesse
    cols = ['EC', 'RPI', 'SS', 'WT', 'pH']
    X    = data[cols].copy()  # Criação de cópia explícita para evitar SettingWithCopyError

    # Convertendo as colunas para numérico e lidando com valores inválidos
    for c in cols:
        X[c] = pd.to_numeric(X[c], errors='coerce')

    # Removendo valores nulos
    X = X.dropna()

    # Definindo variáveis independentes e dependentes
    variable_names = ['EC', 'SS', 'WT', 'pH']
    target_names   = ['RPI']


    # # Normalizando as variáveis independentes
    # scaler            = MinMaxScaler()
    # X[variable_names] = scaler.fit_transform(X[variable_names])


    # Dividindo os dados em treinamento e teste
    X_train, X_test, y_train, y_test = train_test_split(
        X[variable_names],
        X[target_names],
        test_size    = test_size,
        random_state = seed
    )

    # Informações sobre os dados
    n_samples, n_features = X_train.shape
    dataset = {
        'task'         : 'regression',
        'name'         : 'WQ Taiwan',
        'feature_names': np.array(variable_names),
        'target_names' : target_names,
        'n_samples'    : n_samples,
        'n_features'   : n_features,
        'X_train'      : X_train.values,
        'y_train'      : y_train.values.ravel(),
        'X_test'       : X_test.values,
        'y_test'       : y_test.values.ravel(),
        'targets'      : target_names,
        'descriptions' : 'None',
        'reference'    : "https://data.moenv.gov.tw/en/dataset/detail/WQX_P_01",
    }

    return dataset
