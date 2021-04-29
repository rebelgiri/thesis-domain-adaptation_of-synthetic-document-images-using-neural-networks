from classifier_model import *
from datetime import datetime
from matplotlib import pyplot as plt
from sklearn.metrics import classification_report
from preprocessing_images import *
import numpy as np
import sys
import tensorflow as tf
import io
import itertools
import sklearn.metrics
import pathlib

class CustomCallback(tf.keras.callbacks.Callback):

    def __init__(self, model, test_images, test_labels, class_names, log_dir, file_writer_cm, file_name):
        self.model = model
        self.test_images = test_images
        self.test_labels = test_labels
        self.class_names = class_names
        self.log_dir = log_dir
        self.file_writer_cm = file_writer_cm
        self.file_name = file_name

    def on_epoch_end(self, epoch, logs):
        # Use the model to predict the values from the validation dataset.
        test_pred_raw = self.model.predict(self.test_images)
        test_pred = np.argmax(test_pred_raw, axis=1)
        
        # Calculate the confusion matrix.
        cm = sklearn.metrics.confusion_matrix(self.test_labels, test_pred)
        # Log the confusion matrix as an image summary.
        figure = plot_confusion_matrix(cm, class_names=self.class_names, file_name=self.file_name)
        cm_image = plot_to_image(figure)

        # Log the confusion matrix as an image summary.
        with self.file_writer_cm.as_default():
          tf.summary.image("Confusion Matrix", cm_image, step=epoch)
  

def plot_to_image(figure):
  """Converts the matplotlib plot specified by 'figure' to a PNG image and
  returns it. The supplied figure is closed and inaccessible after this call."""
  # Save the plot to a PNG in memory.
  buf = io.BytesIO()
  plt.savefig(buf, format='png')
  # Closing the figure prevents it from being displayed directly inside
  # the notebook.
  plt.close(figure)
  buf.seek(0)
  # Convert PNG buffer to TF image
  image = tf.image.decode_png(buf.getvalue(), channels=4)
  # Add the batch dimension
  image = tf.expand_dims(image, 0)
  return image


def plot_confusion_matrix(cm, class_names, file_name):
  """
  Returns a matplotlib figure containing the plotted confusion matrix.

  Args:
    cm (array, shape = [n, n]): a confusion matrix of integer classes
    class_names (array, shape = [n]): String names of the integer classes
  """
  figure = plt.figure(figsize=(12, 12), dpi=200)
  plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
  plt.title("Confusion matrix")
  plt.colorbar()
  tick_marks = np.arange(len(class_names))
  plt.xticks(tick_marks, class_names, rotation=90)
  plt.yticks(tick_marks, class_names)

  # Compute the labels from the normalized confusion matrix.
  labels = np.around(cm.astype('float') / cm.sum(axis=1)[:, np.newaxis], decimals=2)

  # Use white text if squares are dark; otherwise black.
  threshold = cm.max() / 2.
  for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
    color = "white" if cm[i, j] > threshold else "black"
    plt.text(j, i, labels[i, j], horizontalalignment="center", color=color)

  plt.tight_layout()
  plt.ylabel('True label')
  plt.xlabel('Predicted label')
  plt.savefig(file_name)
  return figure

def image_grid(train_images, class_names, train_labels):
  """Return a 2x5 grid of the MNIST images as a matplotlib figure."""
  # Create a figure to contain the plot.
  figure = plt.figure(figsize=(20,20))
  for i in range(10):
    # Start next subplot.
    plt.subplot(2, 5, i + 1, title=class_names[train_labels[i]])
    plt.xticks([])
    plt.yticks([])
    plt.grid(False)
    plt.imshow(train_images[i], cmap=plt.cm.binary)
    #image = np.squeeze(train_images[i])
    #plt.imshow(image, cmap=plt.cm.binary)

  return figure


if __name__ == "__main__":

    print(f"Arguments count: {len(sys.argv)}")
    classifier_training_data_set_path = sys.argv[1]
    classifier_test_data_set_path = sys.argv[2]
    confusion_matrix_image_name = sys.argv[3]

    print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))

    data_dir = pathlib.Path(classifier_training_data_set_path)
    list_ds = tf.data.Dataset.list_files(str(data_dir/'*/*'))

    test_data_dir = pathlib.Path(classifier_test_data_set_path)
    test_ds = tf.data.Dataset.list_files(str(test_data_dir/'*/*'))

    class_names = np.array(sorted([item.name for item in data_dir.glob('*')]))
    print(class_names)  

    image_count = len(list(data_dir.glob('*/*.png')))
    print(image_count)

    val_size = int(image_count * 0.2)
    train_ds = list_ds.skip(val_size)
    val_ds = list_ds.take(val_size)


    print(tf.data.experimental.cardinality(train_ds).numpy())
    print(tf.data.experimental.cardinality(val_ds).numpy())
    print(tf.data.experimental.cardinality(test_ds).numpy())


    train_ds = train_ds.map(lambda x: preprocess_classifier_images(x, class_names), 
      num_parallel_calls=tf.data.experimental.AUTOTUNE)

    val_ds = val_ds.map(lambda x: preprocess_classifier_images(x, class_names),
      num_parallel_calls=tf.data.experimental.AUTOTUNE)

    test_ds = test_ds.map(lambda x: preprocess_classifier_images(x, class_names),
      num_parallel_calls=tf.data.experimental.AUTOTUNE)

    
    train_ds = configure_for_performance(train_ds, 10, 
      tf.data.experimental.cardinality(train_ds).numpy())
    val_ds = configure_for_performance(val_ds, 10,
      tf.data.experimental.cardinality(val_ds).numpy())
    test_ds = configure_for_performance(test_ds, 1162,
      tf.data.experimental.cardinality(test_ds).numpy())

    for image, label in train_ds.take(1):
        print("Image shape: ", image.numpy().shape)
        print("Label: ", label.numpy())

    time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # Tensorboard Logging

    log_dir = "logs/fit/" + time
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)

    # Creates a file writer for the log directory.
    file_writer_cm = tf.summary.create_file_writer(log_dir + '/cm')
    file_writer = tf.summary.create_file_writer(log_dir)
    with file_writer.as_default():
      batchX, batchY = next(iter(train_ds))
      tf.summary.image("10 training data examples", batchX, max_outputs=25, step=0)
 
    # Prepare the plot
    figure = image_grid(batchX, class_names, np.argmax(batchY, axis=-1))
    # Convert to image and log
    with file_writer.as_default():
      tf.summary.image("Training data", plot_to_image(figure), step=0)

    # retrieve the test data
    X_test, y_test = next(iter(test_ds))

    # create classifier model
    type_of_the_classifier = 'synthetic_documents_classifier'
    file_name = confusion_matrix_image_name + '_' + time
    # Example:  Confusion_Matrix_Synthetic_Data_Classifier
    # Example:  Confusion_Matrix_Faxified_Data_Classifier
    
    synthetic_documents_classifier_model = create_model(10)     

    synthetic_documents_classifier_model.fit(
            train_ds,
            epochs=15,
            validation_data=val_ds,
            callbacks=[tensorboard_callback, CustomCallback(synthetic_documents_classifier_model, 
            X_test,
            np.argmax(y_test, axis=-1),
            class_names,
            log_dir,
            file_writer_cm,
            file_name
            )]
            )
          
    print('Training Finished...')
    # serialize weights to HDF5
    synthetic_documents_classifier_model.save(type_of_the_classifier + '_' + time + '_model.h5')
    
    synthetic_documents_classifier_logs =  open('synthetic_documents_classifier_logs' + 
    '_' + time + '.txt', 'a')

    print('Saved model to disk ' + type_of_the_classifier + '_' + time + '_model.h5', 
    file=synthetic_documents_classifier_logs)

    y_test_pred = np.argmax(synthetic_documents_classifier_model.predict(X_test), axis=-1)
    y_test_real = np.argmax(y_test, axis=-1)

    results = synthetic_documents_classifier_model.evaluate(X_test, y_test, verbose=2)
    print(classification_report(y_test_real, y_test_pred, target_names=class_names, zero_division=1), file=synthetic_documents_classifier_logs)
    print("test loss, test acc:", results, file=synthetic_documents_classifier_logs)

    # serialize weights to HDF5
    synthetic_documents_classifier_model.save(type_of_the_classifier + '_' + time + '_model.h5')

    synthetic_documents_classifier_logs.close()

   