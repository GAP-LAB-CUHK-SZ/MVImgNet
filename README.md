# MVImgNet: A Large-scale Dataset of Multi-view Images
<img src="./assets/teaser_ori.png" width="900"/>

by [Xianggang Yu*](https://larry-u.github.io/), [Mutian Xu*†](https://mutianxu.github.io/), [Yidan Zhang*](http://zhangyidan.xyz/), Haolin Liu*, Chongjie Ye*,
Yushuang Wu, Zizheng Yan, Chenming Zhu, Zhangyang Xiong, Tianyou Liang,
[Guanying Chen](https://guanyingc.github.io/), Shuguang Cui, [Xiaoguang Han‡](https://gaplab.cuhk.edu.cn/) from [GAP-Lab](https://gaplab.cuhk.edu.cn/).

## Update
[MVImgNet2.0](https://github.com/luyues/MVImgNet2.0) is released! It expands MVImgNet to a total of ~520k real-life objects and 515 categories, contains ∼300k real-world objects in 340+ classes. The annotation comprehensively covers object masks, camera parameters, and point clouds.

## Introduction
This repository is built for:

**MVImgNet**: A Large-scale Dataset of Multi-view Images **(CVPR2023)** [[arXiv](http://arxiv.org/abs/2303.06042)]


If you find our work useful in your research, please consider citing:
```
@inproceedings{yu2023mvimgnet,
    title     = {MVImgNet: A Large-scale Dataset of Multi-view Images},
    author    = {Yu, Xianggang and Xu, Mutian and Zhang, Yidan and Liu, Haolin and Ye, Chongjie and Wu, Yushuang and Yan, Zizheng and Liang, Tianyou and Chen, Guanying and Cui, Shuguang and Han, Xiaoguang},
    booktitle = {CVPR},
    year      = {2023}
}
}
```

## MVImgNet
MVImgNet contains **6.5 million** frames from **219,188** videos crossing objects from **238** classes. We provide an OneDrive link to download the full data. Please fill out this [form](https://docs.google.com/forms/d/e/1FAIpQLSfU9BkV1hY3r75n5rc37IvlzaK2VFYbdsvohqPGAjb2YWIbUg/viewform?usp=sf_link) to get the download link and password.

**NOTE**: 
- We split the *full* data into 42 zip files, the total size is about 3.4 TB. If you need the *full* dataset, please directly download all `mvi_xx.zip`.

- If you just need *some categories* of the data, please download the corresponding categories at `MVImgNet_by_categories`, where we split the dataset into different categories (but it is *incomplete*, some categories are not included).

### Usage
```
cd path/to/mvimgnet_zip_file
unzip './*.zip'
```

### Folder structure
```
|-- ROOT
    |-- class_label
        |-- instance_id
            |-- images
            |-- sparse/0
                |-- cameras.bin   # COLMAP reconstructed cameras
                |-- images.bin    # binary data of input images
                |-- points3D.bin  # COLMAP reconstructed sparse point cloud (not dense) 
```

The mapping between `class_label` and class name can be found in [mvimgnet_category.txt](https://github.com/GAP-LAB-CUHK-SZ/MVImgNet/blob/main/mvimgnet_category.txt).

The `images` folder contains the multi-view images, and the `sparse` folder contains the reconstructed camera parameters using COLMAP. It is recommended to use the functions provided by [COLMAP](https://github.com/colmap/colmap/blob/dev/scripts/python/read_write_model.py) to read the binary files under `sparse` folder. Moreover, the `gen_poses` function from [this repo](https://github.com/Fyusion/LLFF/tree/master/llff/poses) is recommended to convert the poses for NeRF training.

### Script for downloading MVImgNet
We also provide the script, at [download_tool.zip](https://github.com/GAP-LAB-CUHK-SZ/MVImgNet/blob/main/download_tool.zip), for downloading all the content of our dataset. Before using it, please make sure you have filled out our form and get the password. 

Update 2025.Jul.8th
We renew the download script to fix: 
1. The SharePoint authentication may interrupt the download process.
2. Users can now choose the specific folder to download the MVImgNet

Usage: 
1. Unzip the download_tool.zip using the password offered in [form](https://docs.google.com/forms/d/e/1FAIpQLSfU9BkV1hY3r75n5rc37IvlzaK2VFYbdsvohqPGAjb2YWIbUg/viewform?usp=sf_link)
2. Choose the subfolder to download. [MVImgNet_origin, MVImgNet_category, MVImgNet_mask]
3. Download with:
```
python download_tool.py --data_name "MVImgNet_origin" --download_folder "/path/you/want/to/save"
```

## MVPNet
MVPNet now contains 87,825 point clouds from 180 categories. Please fill out the following [form](https://docs.google.com/forms/d/e/1FAIpQLSeZlpezgzmCufD94meHv-Pl_54RpNu2jZqMsyW2GCkVouyomQ/viewform?usp=sf_link) to download MVPNet.

## Demo
MVImgNet is also shown by Voxel51 at [here](https://cvpr.fiftyone.ai/datasets/mvimgnet/samples), which is publicly demo-able!

## License

The data is released under the MVImgNet Terms of Use, and the code is released under the Attribution-NonCommercial 4.0 International License.

Copyright (c) 2023

## Acknowledgement

Thanks to [Wei Cheng](https://wchengad.github.io/) for the new downloading solution for our dataset.

Thanks to [Gege Gao](https://github.com/GGGHSL) for providing tips on downloading our dataset.

Thanks to [Voxel51](https://docs.voxel51.com/) for providing the dataset demo.
