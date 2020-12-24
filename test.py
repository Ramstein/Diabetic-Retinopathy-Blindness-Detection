hyperparameters = {
    # 'seed': 42,
    # 'fast': "",
    # 'mixup': "",
    # 'balance': "",
    # 'balance-datasets': "",
    # 'swa': "",
    # 'show': "",
    # 'use-idrid':"",
    # 'use-messidor':"",
    # 'use-aptos-2015': "",
    'use-aptos-2019': "",
    'verbose': "",
    # 'coarse': "",
    # 'accumulation-steps': 1,
    'data-dir': "/opt/ml/input/data",
    'model': 'efficientb6_max',
    'batch-size': 64,
    'epochs': 10,
    'early-stopping': 20,
    'fold': 3,
    # 'freeze-encoder': "",
    'learning-rate': 3e-4,
    # 'criterion-log': ['mse'],
    # 'criterion-crd': None,
    'criterion-cls': 'focal_kappa',
    'l1': 2e-4,
    # 'l2': 0,
    'optimizer': 'Adam',
    # 'preprocessing': None,
    # 'checkpoint': None,
    'workers': 4,
    # 'augmentations': 'medium',
    # 'tta': None,
    # 'transfer': None,
    'fp16': "",
    'scheduler': 'multistep',
    'size': 512,
    # 'weight-decay': 0.0,
    # 'weight-decay-step': None,
    'dropout': 0.0,
    # 'warmup': 10,
    # 'experiment': None,
}