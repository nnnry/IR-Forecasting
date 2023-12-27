import os 
import warnings

warnings.filterwarnings("ignore")

import copy
from pathlib import Path

import lightning.pytorch as pl
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor
from lightning.pytorch.loggers import TensorBoardLogger

import numpy as np
import pandas as pd
import torch

from pytorch_forecasting import Baseline, TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer, MultiNormalizer
from pytorch_forecasting.metrics import MAE, MAPE, SMAPE, PoissonLoss, RMSE, QuantileLoss, MultiHorizonMetric, MultiLoss
from pytorch_forecasting.models.temporal_fusion_transformer.tuning import optimize_hyperparameters

data = pd.read_csv("relationValue.csv", sep = "\t")
# data["meanVal"] = data["meanVal"]*5
data["time_idx"] = data.groupby("yearmonth")["yearmonth"].ngroup()
data["yearmonth"] = data["yearmonth"].astype(str)
data["month"] = data["yearmonth"].str[4:]
data.sample(10)

max_prediction_length = 6
max_encoder_length = 12
training_cutoff = data["time_idx"].max() - (max_prediction_length+6)

training = TimeSeriesDataSet(
    data[lambda x: x.time_idx <= training_cutoff],
    time_idx = "time_idx",
    target = "meanVal",
    group_ids = ["actor1"],
    min_encoder_length=max_encoder_length,
    max_encoder_length=max_encoder_length,
    min_prediction_length=max_prediction_length,
    max_prediction_length=max_prediction_length,
    static_categoricals=["actor1","actor2"],
    static_reals=[],
    time_varying_known_categoricals=["yearmonth", "month"],
    time_varying_known_reals = [],
    # time_varying_unknown_reals = ["impressionVal",	"accumulativeVal",	"deepVal","windowMeanVal","meanVal", "interactionVal"],
    time_varying_unknown_reals = ["meanVal"],

    add_relative_time_idx=False,
    add_target_scales=True,
    add_encoder_length=True,
)

validation = TimeSeriesDataSet(
    data[lambda x: x.time_idx > training_cutoff-max_encoder_length+1],
    time_idx = "time_idx",
    target = "meanVal",
    group_ids = ["actor1"],
    min_encoder_length=max_encoder_length,
    max_encoder_length=max_encoder_length,
    min_prediction_length=max_prediction_length,
    max_prediction_length=max_prediction_length,
    static_categoricals=["actor1","actor2"],
    static_reals=[],
    time_varying_known_categoricals=["yearmonth","month"],
    time_varying_known_reals = [],
    # time_varying_unknown_reals = ["impressionVal",	"accumulativeVal",	"deepVal","windowMeanVal","meanVal", "interactionVal"],
    time_varying_unknown_reals = ["meanVal"],

    add_relative_time_idx=False,
    add_target_scales=True,
    add_encoder_length=True,
)

# validation = TimeSeriesDataSet.from_dataset(training, data, predict=True, stop_randomization=True)

batch_size = 64  # set this between 32 to 128
train_dataloader = training.to_dataloader(train=True, batch_size=batch_size, num_workers=0)
val_dataloader = validation.to_dataloader(train=False, batch_size=batch_size * 10, num_workers=0)

baseline_predictions = Baseline().predict(val_dataloader, return_y=True)

pl.seed_everything(42)
# trainer = pl.Trainer(
#     accelerator="gpu",
#     # clipping gradients is a hyperparameter and important to prevent divergance
#     # of the gradient for recurrent neural networks
#     gradient_clip_val=0.1,
# )


# tft = TemporalFusionTransformer.from_dataset(
#     training,
#     # not meaningful for finding the learning rate but otherwise very important
#     learning_rate=0.03,
#     hidden_size=8,  # most important hyperparameter apart from learning rate
#     # number of attention heads. Set to up to 4 for large datasets
#     attention_head_size=1,
#     dropout=0.1,  # between 0.1 and 0.3 are good values
#     hidden_continuous_size=8,  # set to <= hidden_size
#     loss=QuantileLoss(),
#     optimizer="Ranger"
#     # reduce learning rate if no improvement in validation loss after x epochs
#     # reduce_on_plateau_patience=1000,
# )
# print(f"Number of parameters in network: {tft.size()/1e3:.1f}k")

# #find optimal learning rate
# from lightning.pytorch.tuner import Tuner

# res = Tuner(trainer).lr_find(
#     tft,
#     train_dataloaders=train_dataloader,
#     val_dataloaders=val_dataloader,
#     max_lr=10.0,
#     min_lr=1e-6,
# )

# print(f"suggested learning rate: {res.suggestion()}")
# fig = res.plot(show=True, suggest=True)
# fig.show()

early_stop_callback = EarlyStopping(monitor="val_loss", min_delta=1e-4, patience=20, verbose=False, mode="min")
lr_logger = LearningRateMonitor()  # log the learning rate
logger = TensorBoardLogger("lightning_logs")  # logging results to a tensorboard

trainer = pl.Trainer(  
    max_epochs=160,
    accelerator="gpu",
    # devices=1,
    enable_model_summary=True,
    gradient_clip_val=0.01144,
    # limit_train_batches=50,  # coment in for training, running valiation every 30 batches
    # fast_dev_run=True,  # comment in to check that networkor dataset has no serious bugs
    callbacks=[lr_logger, early_stop_callback],
    logger=logger,
)



tft = TemporalFusionTransformer.from_dataset(
    training,
    learning_rate=0.0014,
    hidden_size=20,
    attention_head_size=1,
    dropout=0.2616,
    hidden_continuous_size=10,
    loss=QuantileLoss(),
    log_interval=10,  # uncomment for learning rate finder and otherwise, e.g. to 10 for logging every 10 batches
    optimizer="Ranger",
    reduce_on_plateau_patience=4,
)
print(f"Number of parameters in network: {tft.size()/1e3:.1f}k")

trainer.fit(
    tft,
    train_dataloaders=train_dataloader,
    val_dataloaders=val_dataloader,
)


# load the best model according to the validation loss
# (given that we use early stopping, this is not necessarily the last epoch)
best_model_path = trainer.checkpoint_callback.best_model_path
best_tft = TemporalFusionTransformer.load_from_checkpoint(best_model_path)
predictions = best_tft.predict(val_dataloader, return_y=True, trainer_kwargs=dict(accelerator="gpu"), return_x=True, return_index = True, return_decoder_lengths= True)


# print("Trained model MAE:",MAE()(predictions.output, predictions.y))
print(">>>Baseline model MAE:", MAE()(baseline_predictions.output, baseline_predictions.y))
print(">>>Baseline model MAPE:", MAPE()(baseline_predictions.output, baseline_predictions.y))
print(">>>Trained model MAE:",MAE()(predictions.output, predictions.y))
print(">>>Trained model MAPE:",MAPE()(predictions.output, predictions.y))
raw_predictions = best_tft.predict(val_dataloader, mode="raw", return_x=True)

for idx in range(10):  # plot 10 examples
    best_tft.plot_prediction(raw_predictions.x, raw_predictions.output, idx=idx, add_loss_to_title=True)

best_tft.plot_prediction(raw_predictions.x, raw_predictions.output, idx=idx, add_loss_to_title=True)

import matplotlib.pyplot as plt
fig, ax = plt.subplots()
plt.xlabel("month (2022-2023)")
plt.ylabel("value")

count = 0
for j in range(6):
    myindexs = []
    myoutput = []
    myactual = []
    for i in range(6):
        myindex = predictions.index.time_idx[i]+j
        myindex = data.loc[data["time_idx"] == myindex, "month"].iloc[0]
        myindexs.append(myindex)
        
        myoutput.append(predictions.output[i][0+j].cpu().numpy())
        myactual.append(predictions.y[0][i][0+j].cpu().numpy())
        count += 1
        if count == 7:
            ax.legend(loc = "upper right")
    ax.plot(myindexs, myactual, color = "steelblue", label = "observed")
    ax.plot(myindexs, myoutput, color = "orange", label = "predicted")