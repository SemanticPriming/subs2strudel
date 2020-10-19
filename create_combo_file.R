# Libraries  --------------------------------------------------------------

# deal with working directory
# assumes you are using a r project
library(here)
setwd(here())

# libraries
library(plyr)
library(rio)

# settings
language <- "eu" #two letter code

# Read in files -----------------------------------------------------------

# grab the files
file_names <- list.files(path = "concept-feature", pattern = language,
                         full.names = T)

# import and put together
imported_files <- import_list(file_names,
                              rbind = TRUE,
                              rbind_fill = TRUE)

# drop the file column
imported_files$`_file` <- NULL

# Condense and Finalize ---------------------------------------------------

count_df <- plyr::count(imported_files, 
                        var = colnames(imported_files)[-length(colnames(imported_files))], 
                        wt_var = "freq")

write.csv(count_df, 
          file = paste0("concept-feature/", language, "_concept_features.csv"),
          row.names = F)
