.. _deploy:

########################
build and rollout system
########################

.. todo:: write about core4 build and deploy features


coco --init project1 "test project 1"

coco --build
coco --release

python3 deploy.py project1 file:///home/mra/PycharmProjects/project1/.repos@0.0.1
