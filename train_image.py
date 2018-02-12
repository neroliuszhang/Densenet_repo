# Brief:     Train a densenet for image classification
# Data:      24/Aug./2017
# E-mail:    huyixuanhyx@gmail.com
# License:   Apache 2.0
# By:        Yeephycho @ Hong Kong

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
import os

import net.densenet as densenet
import config as config
import data_provider.data_provider as data_provider
import cv2
import os

os.environ["CUDA_VISIBLE_DEVICES"]=""
FLAGS = tf.app.flags.FLAGS
TRAINING_SET_SIZE = FLAGS.TRAINING_SET_SIZE
BATCH_SIZE = FLAGS.BATCH_SIZE
starter_learning_rate = FLAGS.INIT_LEARNING_RATE
exp_decay_steps = FLAGS.DECAY_STEPS
exp_decay_rate = FLAGS.DECAY_RATE



def densenet_train():
    image_batch_placeholder = tf.placeholder(tf.float32, shape=[None, 224, 224, 3])
    label_batch_placeholder = tf.placeholder(tf.float32, shape=[None, 7])
    if_training_placeholder = tf.placeholder(tf.bool, shape=[])

    image_batch, label_batch, filename_batch = data_provider.feed_data(if_random = True, if_training = True)

    if_training = tf.Variable(True, name='if_training', trainable=False)

    logits = densenet.densenet_inference(image_batch_placeholder, if_training_placeholder, dropout_prob=0.7)

    loss = tf.reduce_sum(tf.nn.softmax_cross_entropy_with_logits(labels=label_batch_placeholder, logits=logits))
    #loss = tf.losses.mean_squared_error(labels=label_batch_placeholder, predictions=logits)
    tf.summary.scalar('loss', loss) # create a summary for training loss

    regularzation_loss = sum(tf.get_collection("regularzation_loss"))
    tf.summary.scalar('regularzation_loss', regularzation_loss)

    total_loss = regularzation_loss + loss
    tf.summary.scalar('total_loss', total_loss)

    global_step = tf.Variable(0, name='global_step', trainable=False)

    learning_rate = tf.train.exponential_decay(learning_rate=starter_learning_rate,
                                               global_step=global_step,
                                               decay_steps=exp_decay_steps,
                                               decay_rate=exp_decay_rate,
                                               staircase=True)
    tf.summary.scalar('learning_rate', learning_rate)

    train_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss=total_loss, global_step=global_step)

    summary_op = tf.summary.merge_all()  # merge all summaries into a single "operation" which we can execute in a session

    saver = tf.train.Saver()

    config = tf.ConfigProto()
    config.gpu_options.allow_growth=True
    sess = tf.Session(config=config)

    summary_writer = tf.summary.FileWriter("./log", sess.graph)

    sess.run(tf.global_variables_initializer())

    checkpoint = tf.train.get_checkpoint_state("./models")
    if(checkpoint != None):
        tf.logging.info("Restoring full model from checkpoint file %s",checkpoint.model_checkpoint_path)
        saver.restore(sess, checkpoint.model_checkpoint_path)

    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(coord=coord, sess = sess)

    check_points = int(TRAINING_SET_SIZE/BATCH_SIZE)
    for epoch in range(250):
        for check_point in range(check_points):
            #print("check point:%d" %(check_point))
            image_batch_train, label_batch_train, filename_train = sess.run([image_batch, label_batch, filename_batch])
            image_batch_squeeze=np.squeeze(image_batch_train)
            cv2.imshow("image show",image_batch_squeeze.astype(np.uint8))
            cv2.waitKey()


            # _, training_loss, _global_step, summary = sess.run([train_step, loss, global_step, summary_op],
            #                                      feed_dict={image_batch_placeholder: image_batch_train,
            #                                                 label_batch_placeholder: label_batch_train,
            #                                                 if_training_placeholder: if_training})

        #     if(bool(check_point%10 == 0) & bool(check_point != 0)):
        #         #print(_)
        #         print("batch: ", check_point + epoch * check_points)
        #         print("training loss: ", training_loss)
        #         summary_writer.add_summary(summary, _global_step)
        #
        # saver.save(sess, "./models/densenet.ckpt", _global_step)

    coord.request_stop()
    coord.join(threads)
    sess.close()
    return 0



# def main():
#     tf.reset_default_graph()
#     densenet_train()



if __name__ == '__main__':
    tf.reset_default_graph()
    densenet_train()



# weights = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES)
# print("")
# for w in weights:
#     shp = w.get_shape().as_list()
#     print("- {} shape:{} size:{}".format(w.name, shp, np.prod(shp)))
# print("")
