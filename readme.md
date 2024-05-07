    __________            _____                          _____            _____
    ___  ____/_____ ________  /__________________  __    __  /______________  /_
    __  /_   _  __ `/  ___/  __/  __ \_  ___/_  / / /    _  __/  _ \_  ___/  __/
    _  __/   / /_/ // /__ / /_ / /_/ /  /   _  /_/ /     / /_ /  __/(__  )/ /_
    /_/      \__,_/ \___/ \__/ \____//_/    _\__, /      \__/ \___//____/ \__/
                                            /____/

## Aerich

1.  aerich init-db [No need to repeat]

At this point, we have created migration for our app and we can see the migration file in the directory

2.  aerich migrate --name add_xxx
3.  aerich upgrade

## 数据字典

1. `data`目录下存放`json`数据字典
2. `mate_model_list.json`:存放不同分组的型号列表配置,供料号新增时选择
3. `mate_model_group.json`: 按不同类别配置型号,例如**感应板**，**设备**，**控制箱**等，用于过滤料号，不同类型的型号->料号进行分组
