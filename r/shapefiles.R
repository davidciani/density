library(tidyverse)
library(fs)
library(sf)
library(units)


DATA_DIR = path("/Users/david/data_projects/datasets-nobackup")


tabblock20 = dir_ls(path(DATA_DIR, "TIGER2020"), glob="*_06_tabblock20.zip") |> 
    map(function(x) st_read("/vsizip/"+x) |> 
            mutate(
                STATEFP20 = as_factor(STATEFP20),
                COUNTYFP20 = as_factor(COUNTYFP20),
                TRACTCE20 = as_factor(TRACTCE20),
                BLOCKCE20 = as_factor(BLOCKCE20),
                NAME20 = as_factor(NAME20),
                MTFCC20 = as_factor(MTFCC20),
                UR20 = as_factor(UR20),
                UACE20 = as_factor(UACE20),
                UATYPE20 = as_factor(UATYPE20),
                FUNCSTAT20 = as_factor(FUNCSTAT20)
            )) |> 
    list_rbind()
