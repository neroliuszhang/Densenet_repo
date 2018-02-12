# Brief:     Data provdier for image classification using tfrecord
# Data:      28/Aug./2017
# E-mail:    huyixuanhyx@gmail.com
# License:   Apache 2.0
# By:        Yeephycho @ Hong Kong


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
import os

import sys
import config as config
from tensorflow.python.ops import random_ops


FLAGS = tf.app.flags.FLAGS
DATA_DIR = FLAGS.train_data_path
TRAINING_SET_SIZE = FLAGS.TRAINING_SET_SIZE
BATCH_SIZE = FLAGS.BATCH_SIZE
IMAGE_SIZE = FLAGS.IMAGE_SIZE



def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))

def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


# image object from tfrecord
class _image_object:
    def __init__(self):
        self.image = tf.Variable([], dtype = tf.string, trainable=False)
        self.height = tf.Variable([], dtype = tf.int64, trainable=False)
        self.width = tf.Variable([], dtype = tf.int64, trainable=False)
        self.filename = tf.Variable([], dtype = tf.string, trainable=False)
        self.label = tf.Variable([], dtype = tf.int32, trainable=False)

def read_and_decode(filename_queue):
    reader = tf.TFRecordReader()
    _, serialized_exampe = reader.read(filename_queue)
    features = tf.parse_single_example(serialized_exampe,
                                       features={
                                           'image_raw': tf.FixedLenFeature([], tf.string),
                                           'height': tf.FixedLenFeature([], tf.int64),
                                           'width': tf.FixedLenFeature([], tf.int64),
                                           'depth': tf.FixedLenFeature([], tf.int64),
                                           'label': tf.FixedLenFeature([], tf.int64)
                                       })
    #image_encoded = features["image_raw"]
    image_raw = tf.decode_raw(features['image_raw'], tf.uint8)
    #image_raw.set_shape([IMAGE_SIZE * 3])
    image_raw = tf.reshape(image_raw, [ 224, 224, 3])
    #print (image_raw)
    image_object = _image_object()
    # image_object.image = tf.image.resize_image_with_crop_or_pad(image_raw, IMAGE_SIZE, IMAGE_SIZE)
    image_object.image = tf.cast(image_raw,tf.float32)
    #tf.image.resize_images(image_raw, [-1,IMAGE_SIZE, IMAGE_SIZE,3], method=0, align_corners=True)
    # image_object.height = features["height"]
    # image_object.width = features["width"]
    # #image_object.filename = features["image/filename"]


    image_object.label = tf.cast(features["label"], tf.int64)
    return image_object
#flip


def feed_data(if_random = True, if_training = True):
    with tf.name_scope('image_reader_and_preprocessor') as scope:
        if(if_training):
            filenames = [os.path.join(DATA_DIR, "train.tfrecords")]
        else:
            filenames = [os.path.join(DATA_DIR, "val.tfrecords")]

        for f in filenames:
            if not tf.gfile.Exists(f):
                raise ValueError("Failed to find file: " + f)
        #print("read name:")
        filename_queue = tf.train.string_input_producer(filenames)
        image_object = read_and_decode(filename_queue)

        if(if_training):
            print(image_object.image.get_shape())
            image = tf.cast(tf.image.random_flip_left_right(image_object.image), tf.float32)
            ##################queenie edited##################################

            # bright_dice=random_ops.random_uniform([],0,2,dtype=tf.int32,seed=None)
            # bright=random_ops.random_uniform([],0.0,1.2,seed=None)*tf.to_float(bright_dice)#######origin 0.06
            image = tf.cast(tf.image.random_brightness(image,0.06),tf.float32)

            #####################################################################
            # image = tf.image.adjust_gamma(tf.cast(image_object.image, tf.float32), gamma=1, gain=1) # Scale image to (0, 1)
            # image = tf.image.per_image_standardization(image)
        else:
            image = tf.cast(image_object.image, tf.float32)
            # image = tf.image.per_image_standardization(image_object.image)

        label = image_object.label
        filename = image_object.filename

        if(if_training):
            num_preprocess_threads = 1
        else:
            num_preprocess_threads = 1

        if(if_random):
            min_fraction_of_examples_in_queue = 0.4
            min_queue_examples = int(TRAINING_SET_SIZE * min_fraction_of_examples_in_queue)
            print("Filling queue with %d images before starting to train. " "This will take some time." % min_queue_examples)
            image_batch, label_batch, filename_batch = tf.train.shuffle_batch(
                [image, label, filename],
                batch_size = BATCH_SIZE,
                num_threads = num_preprocess_threads,
                capacity = min_queue_examples + 3 * BATCH_SIZE,
                min_after_dequeue = min_queue_examples)
            image_batch = tf.reshape(image_batch, (BATCH_SIZE, IMAGE_SIZE, IMAGE_SIZE, 3))
            label_offset = -tf.ones([BATCH_SIZE], dtype=tf.int64, name="label_batch_offset")
            label_batch = tf.one_hot(tf.add(label_batch, label_offset), depth=7, on_value=1.0, off_value=0.0)
        else:
            image_batch, label_batch, filename_batch = tf.train.batch(
                [image, label, filename],
                batch_size = BATCH_SIZE,
                num_threads = num_preprocess_threads)
            image_batch = tf.reshape(image_batch, (BATCH_SIZE, IMAGE_SIZE, IMAGE_SIZE, 3))
            label_offset = -tf.ones([BATCH_SIZE], dtype=tf.int64, name="label_batch_offset")
            label_batch = tf.one_hot(tf.add(label_batch, label_offset), depth=7, on_value=1.0, off_value=0.0)
    return image_batch, label_batch, filename_batch
