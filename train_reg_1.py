from __future__ import absolute_import

import argparse
import collections
import json
import multiprocessing
import os
from datetime import datetime
from tqdm import tqdm


import torch
from catalyst.dl import SupervisedRunner, EarlyStoppingCallback
from catalyst.utils import load_checkpoint, unpack_checkpoint
from pytorch_toolbelt.utils import fs
from pytorch_toolbelt.utils.random import set_manual_seed, get_random_name
from pytorch_toolbelt.utils.torch_utils import count_parameters, \
    set_trainable

from retinopathy.callbacks import LPRegularizationCallback, \
    CustomOptimizerCallback
from retinopathy.dataset import get_class_names, \
    get_datasets, get_dataloaders
from retinopathy.factory import get_model, get_optimizer, \
    get_optimizable_parameters, get_scheduler
from retinopathy.scripts.clean_checkpoint import clean_checkpoint
from retinopathy.train_utils import report_checkpoint, get_reg_callbacks, get_ord_callbacks, get_cls_callbacks

import boto3
import botocore
from botocore.exceptions import ClientError

bucket = "dataset-retinopathy"
region_name="us-east-1"


def download_dir(s3_folder, local_path, bucket=""):
    """
    params:
    - s3_folder: pattern to match in s3
    - local_path: local_path path to folder in which to place files
    - bucket: s3 bucket with target contents
    - client: initialized s3 client object
    """
    client = boto3.client('s3', region_name=region_name)
    keys = []
    dirs = []
    next_token = ''
    base_kwargs = {
        'Bucket': bucket,
        'Prefix': s3_folder,
    }
    while next_token is not None:
        kwargs = base_kwargs.copy()
        if next_token != '':
            kwargs.update({'ContinuationToken': next_token})
        results = client.list_objects_v2(**kwargs)
        contents = results.get('Contents')
        for i in contents:
            k = i.get('Key')
            if k[-1] != '/':
                keys.append(k)
            else:
                dirs.append(k)
        next_token = results.get('NextContinuationToken')
    for d in dirs:
        dest_pathname = os.path.join(local_path, d)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
    print("Started downloading the s3://{}/{} to {}".format(bucket, s3_folder, local_path))

    for k in tqdm(keys):
        dest_pathname = os.path.join(local_path, k)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
        try:
            # print("Downloading {}".format(dest_pathname))
            client.download_file(bucket, k, dest_pathname)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("The object does not exist.")
            else:
                raise
    print("Downloading completed the s3://{}/{} to {}".format(bucket, s3_folder, local_path))


def main():
    # downloading the files from s3 first
    download_dir(s3_folder='aptos-2019', local_path='/home/ec2-user/SageMaker/data_full', bucket=bucket)
    parser = argparse.ArgumentParser()
    # parser.add_argument('--seed', type=int, default=42, help='Random seed')
    # parser.add_argument('--fast', action='store_true')
    # parser.add_argument('--mixup', action='store_true')
    # parser.add_argument('--balance', action='store_true')
    # parser.add_argument('--balance-datasets', action='store_true')
    # parser.add_argument('--swa', action='store_true')
    # parser.add_argument('--show', action='store_true')
    # parser.add_argument('--use-idrid', action='store_true')
    # parser.add_argument('--use-messidor', action='store_true')
    # parser.add_argument('--use-aptos2015', action='store_true')
    # parser.add_argument('--use-aptos2019', action='store_true')
    # parser.add_argument('-v', '--verbose', action='store_true')
    # parser.add_argument('--coarse', action='store_true')
    # parser.add_argument('-acc', '--accumulation-steps', type=int, default=1, help='Number of batches to process')
    # parser.add_argument('-dd', '--data-dir', type=str, default='data', help='Data directory')
    # parser.add_argument('-m', '--model', type=str, default='resnet18_gap', help='')
    # parser.add_argument('-b', '--batch-size', type=int, default=8, help='Batch Size during training, e.g. -b 64')
    # parser.add_argument('-e', '--epochs', type=int, default=100, help='Epoch to run')
    # parser.add_argument('-es', '--early-stopping', type=int, default=None,
    #                     help='Maximum number of epochs without improvement')
    # parser.add_argument('-f', '--fold', action='append', type=int, default=None)
    # parser.add_argument('-fe', '--freeze-encoder', action='store_true')
    # parser.add_argument('-lr', '--learning-rate', type=float, default=1e-4, help='Initial learning rate')
    # parser.add_argument('--criterion-reg', type=str, default=['mse'], nargs='+', help='Criterion')
    # parser.add_argument('--criterion-ord', type=str, default=None, nargs='+', help='Criterion')
    # parser.add_argument('--criterion-cls', type=str, default=None, nargs='+', help='Criterion')
    # parser.add_argument('-l1', type=float, default=0, help='L1 regularization loss')
    # parser.add_argument('-l2', type=float, default=0, help='L2 regularization loss')
    # parser.add_argument('-o', '--optimizer', default='Adam', help='Name of the optimizer')
    # parser.add_argument('-p', '--preprocessing', default=None, help='Preprocessing method')
    # parser.add_argument('-c', '--checkpoint', type=str, default=None,
    #                     help='Checkpoint filename to use as initial model weights')
    # parser.add_argument('-w', '--workers', default=multiprocessing.cpu_count(), type=int, help='Num workers')
    # parser.add_argument('-a', '--augmentations', default='medium', type=str, help='')
    # parser.add_argument('-tta', '--tta', default=None, type=str, help='Type of TTA to use [fliplr, d4]')
    # parser.add_argument('-t', '--transfer', default=None, type=str, help='')
    # parser.add_argument('--fp16', action='store_true')
    # parser.add_argument('-s', '--scheduler', default='multistep', type=str, help='')
    # parser.add_argument('--size', default=512, type=int, help='Image size for training & inference')
    # parser.add_argument('-wd', '--weight-decay', default=0.0, type=float, help='L2 weight decay')
    # parser.add_argument('-wds', '--weight-decay-step', default=None, type=float,
    #                     help='L2 weight decay step to add after each epoch')
    # parser.add_argument('-d', '--dropout', default=0.0, type=float, help='Dropout before head layer')
    # parser.add_argument('--warmup', default=0, type=int,
    #                     help='Number of warmup epochs with 0.1 of the initial LR and frozed encoder')
    # parser.add_argument('-x', '--experiment', default=None, type=str, help='Dropout before head layer')

    args = parser.parse_args()

    seed = 42
    data_dir = '/home/ec2-user/SageMaker/data'
    num_workers = 4
    num_epochs = 100
    batch_size = 64
    learning_rate = 1e-4
    l1 = 0.0
    l2 = 0.0
    early_stopping = 20
    model_name = 'efficientb6_max'
    checkpoint_file = None
    optimizer_name = 'Adam'
    image_size = (512, 512)
    fast = False
    augmentations = 'medium'
    transfer=None
    fp16 = True
    freeze_encoder = False
    criterion_reg_name = ['mse']
    criterion_ord_name = None
    criterion_cls_name = None
    folds = [0, 1, 2, 3]
    mixup = False
    balance = False
    balance_datasets = False
    use_swa = False
    show_batches = False
    scheduler_name = 'multistep'
    verbose = True
    weight_decay = 0.0
    use_idrid = False
    use_messidor = False
    use_aptos2015 = False
    use_aptos2019 = True
    warmup = 0
    dropout = 0.4
    use_unsupervised = False
    experiment = None
    preprocessing = None
    weight_decay_step = None
    coarse_grading = False
    class_names = get_class_names(coarse_grading)

    assert use_aptos2015 or use_aptos2019 or use_idrid or use_messidor

    current_time = datetime.now().strftime('%b%d_%H_%M')
    random_name = get_random_name()

    if folds is None or len(folds) == 0:
        folds = [None]

    for fold in folds:
        torch.cuda.empty_cache()
        checkpoint_prefix = f'{model_name}_{512}_{augmentations}'

        if preprocessing is not None:
            checkpoint_prefix += f'_{preprocessing}'
        if use_aptos2019:
            checkpoint_prefix += '_aptos2019'
        if use_aptos2015:
            checkpoint_prefix += '_aptos2015'
        if use_messidor:
            checkpoint_prefix += '_messidor'
        if use_idrid:
            checkpoint_prefix += '_idrid'
        if coarse_grading:
            checkpoint_prefix += '_coarse'

        if fold is not None:
            checkpoint_prefix += f'_fold{fold}'

        checkpoint_prefix += f'_{random_name}'

        if experiment is not None:
            checkpoint_prefix = experiment

        directory_prefix = f'{current_time}/{checkpoint_prefix}'
        log_dir = os.path.join('runs', directory_prefix)
        os.makedirs(log_dir, exist_ok=False)

        config_fname = os.path.join(log_dir, f'{checkpoint_prefix}.json')
        with open(config_fname, 'w') as f:
            train_session_args = vars(args)
            f.write(json.dumps(train_session_args, indent=2))

        set_manual_seed(seed)
        num_classes = len(class_names)


        # made changes for device selection
        model = get_model(model_name, num_classes=num_classes, dropout=dropout)
        if torch.cuda.is_available():
            model = model.cuda()

        if transfer:
            transfer_checkpoint = fs.auto_file(transfer)
            print("Transfering weights from model checkpoint",
                  transfer_checkpoint)
            checkpoint = load_checkpoint(transfer_checkpoint)
            pretrained_dict = checkpoint['model_state_dict']

            for name, value in pretrained_dict.items():
                try:
                    model.load_state_dict(
                        collections.OrderedDict([(name, value)]), strict=False)
                except Exception as e:
                    print(e)

            report_checkpoint(checkpoint)

        if checkpoint_file:
            checkpoint = load_checkpoint(fs.auto_file(checkpoint_file))
            unpack_checkpoint(checkpoint, model=model)
            report_checkpoint(checkpoint)

        train_ds, valid_ds, train_sizes = get_datasets(data_dir=data_dir,
                                                       use_aptos2019=use_aptos2019,
                                                       use_aptos2015=use_aptos2015,
                                                       use_idrid=use_idrid,
                                                       use_messidor=use_messidor,
                                                       use_unsupervised=False,
                                                       coarse_grading=coarse_grading,
                                                       image_size=image_size,
                                                       augmentation=augmentations,
                                                       preprocessing=preprocessing,
                                                       target_dtype=int,
                                                       fold=fold,
                                                       folds=4)

        train_loader, valid_loader = get_dataloaders(train_ds, valid_ds,
                                                     batch_size=batch_size,
                                                     num_workers=num_workers,
                                                     train_sizes=train_sizes,
                                                     balance=balance,
                                                     balance_datasets=balance_datasets,
                                                     balance_unlabeled=False)

        loaders = collections.OrderedDict()
        loaders["train"] = train_loader
        loaders["valid"] = valid_loader

        print('Datasets         :', data_dir)
        print('  Train size     :', len(train_loader), len(train_loader.dataset))
        print('  Valid size     :', len(valid_loader), len(valid_loader.dataset))
        print('  Aptos 2019     :', use_aptos2019)
        print('  Aptos 2015     :', use_aptos2015)
        print('  IDRID          :', use_idrid)
        print('  Messidor       :', use_messidor)
        print('Train session    :', directory_prefix)
        print('  FP16 mode      :', fp16)
        print('  Fast mode      :', fast)
        print('  Mixup          :', mixup)
        print('  Balance cls.   :', balance)
        print('  Balance ds.    :', balance_datasets)
        print('  Warmup epoch   :', warmup)
        print('  Train epochs   :', num_epochs)
        print('  Workers        :', num_workers)
        print('  Fold           :', fold)
        print('  Log dir        :', log_dir)
        print('  Augmentations  :', augmentations)
        print('Model            :', model_name)
        print('  Parameters     :', count_parameters(model))
        print('  Image size     :', image_size)
        print('  Freeze encoder :', freeze_encoder)
        print('  Dropout        :', dropout)
        print('  Classes        :', class_names, num_classes)
        print('Optimizer        :', optimizer_name)
        print('  Learning rate  :', learning_rate)
        print('  Batch size     :', batch_size)
        print('  Criterion (cls):', criterion_cls_name)
        print('  Criterion (reg):', criterion_reg_name)
        print('  Criterion (ord):', criterion_ord_name)
        print('  Scheduler      :', scheduler_name)
        print('  Weight decay   :', weight_decay, weight_decay_step)
        print('  L1 reg.        :', l1)
        print('  L2 reg.        :', l2)
        print('  Early stopping :', early_stopping)

        # model training
        callbacks = []
        criterions = {}

        main_metric = 'reg/kappa'
        if criterion_reg_name is not None:
            cb, crits = get_reg_callbacks(criterion_reg_name, class_names=class_names, show=show_batches)
            callbacks += cb
            criterions.update(crits)

        if criterion_ord_name is not None:
            cb, crits = get_ord_callbacks(criterion_ord_name, class_names=class_names, show=show_batches)
            callbacks += cb
            criterions.update(crits)

        if criterion_cls_name is not None:
            cb, crits = get_cls_callbacks(criterion_cls_name,
                                          num_classes=num_classes,
                                          num_epochs=num_epochs, class_names=class_names, show=show_batches)
            callbacks += cb
            criterions.update(crits)

        if l1 > 0:
            callbacks += [LPRegularizationCallback(start_wd=l1, end_wd=l1, schedule=None, loss_key='l1', p=1)]

        if l2 > 0:
            callbacks += [LPRegularizationCallback(start_wd=l2, end_wd=l2, schedule=None, loss_key='l2', p=2)]

        callbacks += [
            CustomOptimizerCallback()
        ]

        runner = SupervisedRunner(input_key='image')

        # Pretrain/warmup
        if warmup:
            set_trainable(model.encoder, False, False)
            optimizer = get_optimizer('Adam', get_optimizable_parameters(model),
                                      learning_rate=learning_rate)

            runner.train(
                fp16=fp16,
                model=model,
                criterion=criterions,
                optimizer=optimizer,
                scheduler=None,
                callbacks=callbacks,
                loaders=loaders,
                logdir=os.path.join(log_dir, 'warmup'),
                num_epochs=warmup,
                verbose=verbose,
                main_metric=main_metric,
                minimize_metric=False,
                checkpoint_data={"cmd_args": vars(args)}
            )

            del optimizer

        if early_stopping:
            callbacks += [
                EarlyStoppingCallback(early_stopping,
                                      min_delta=1e-4,
                                      metric=main_metric, minimize=False)]

        # Main train
        set_trainable(model.encoder, True, False)
        if freeze_encoder:
            set_trainable(model.encoder, trainable=False, freeze_bn=False)

        optimizer = get_optimizer(optimizer_name, get_optimizable_parameters(model),
                                  learning_rate=learning_rate,
                                  weight_decay=weight_decay)

        if use_swa:
            from torchcontrib.optim import SWA
            optimizer = SWA(optimizer,
                            swa_start=len(train_loader),
                            swa_freq=512)

        scheduler = get_scheduler(scheduler_name, optimizer,
                                  lr=learning_rate,
                                  num_epochs=num_epochs,
                                  batches_in_epoch=len(train_loader))

        runner.train(
            fp16=fp16,
            model=model,
            criterion=criterions,
            optimizer=optimizer,
            scheduler=scheduler,
            callbacks=callbacks,
            loaders=loaders,
            logdir=log_dir,
            num_epochs=num_epochs,
            verbose=verbose,
            main_metric=main_metric,
            minimize_metric=False,
            checkpoint_data={"cmd_args": vars(args)}
        )

        del runner, callbacks, loaders, optimizer, model, criterions, scheduler

        best_checkpoint = os.path.join(log_dir, 'checkpoints', 'best.pth')
        model_checkpoint = os.path.join(log_dir, 'checkpoints', f'{checkpoint_prefix}.pth')
        clean_checkpoint(best_checkpoint, model_checkpoint)


if __name__ == '__main__':
    with torch.autograd.detect_anomaly():
        main()