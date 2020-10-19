# Libraries  --------------------------------------------------------------

# deal with working directory
# assumes you are using a r project
library(here)
setwd(here())

#libraries
library(udpipe)
library(NCmisc)
library(tm)
library(plyr)

# settings
download_file <- TRUE # if you want to download the file directly
language <- "af" #two letter language code
model_language <- "afrikaans-afribooms" #what language for POS 
download_model <- TRUE
mac <- TRUE

# Import Subtitle Data ----------------------------------------------------

# save and store a gzipped text file from
#  http://opus.nlpl.eu/OpenSubtitles.php
# make sure to download the datafile from the second table 
#  under 'Statistics and TMX/Moses Downloads'

# download file 
if(download_file){
  # the URL
  con <- paste("http://opus.nlpl.eu/download.php?f=OpenSubtitles/v2018/mono/OpenSubtitles.",
               language, ".gz", sep="")
  # download the file
  download.file(con, 
                destfile = paste0("data/", language, ".gz"),
                mode = "wb")
  
  text_file <- gunzip(filename = paste0("data/", language, ".gz"),
                      destname = paste0("data/", language, ".txt"))
  
  file.split(text_file,
             size = 100000,
             same.dir = TRUE, verbose = TRUE,
             suf = "part", win = TRUE)
}

file_names <- list.files(path = "data", pattern = "part",
                         full.names = T)

for (file in file_names){
  # Preprocess text ---------------------------------------------------------
  
  data.text <- readLines(file,
                         encoding = "UTF-8")
  
  data.text <- tolower(data.text)
  data.text <- tm::stripWhitespace(data.text)
  
  # Annotate the Text -------------------------------------------------------
  #  Download the language model 
  if(download_model){
    dl <- udpipe_download_model(language = model_language) 
    download_model <- FALSE
  }
  
  #  Annotate the text
  annotate <- udpipe(data.text, model_language) 
  # Convert to dataframe
  annotated_df <- as.data.frame(annotate) 
  
  
  # Use Dependencies --------------------------------------------------------
  
  # make a unique id of doc, token_id - this tells you the original word in the sentence
  token_dictionary <- annotated_df[ , c("token", "lemma", "doc_id", "token_id", "upos") ]
  token_dictionary$unique_id <- paste0(token_dictionary$doc_id, "-", token_dictionary$token_id)
  token_dictionary <- token_dictionary[ , c("token", "lemma", "unique_id", "upos")]
  
  # make a unique id of doc, head_token_id - this tells you the head id
  annotated_df$unique_id <- paste0(annotated_df$doc_id, "-", annotated_df$head_token_id)
  
  # merge those together to get the head for each original token 
  annotated_df_lemma <- merge(annotated_df, token_dictionary, by = "unique_id")
  
  # filter out columns we no longer need
  annotated_df_lemma <- annotated_df_lemma[ , c("token.x", "lemma.x", "upos.x", 
                                                "feats", "dep_rel", "token.y",
                                                "lemma.y", "upos.y")]
  
  # rename for clarity
  colnames(annotated_df_lemma) <- c("feature_token", "feature_lemma", "feature_pos", 
                                    "characteristics", "dependency_relation", "concept_token", 
                                    "concept_lemma", "concept_pos")
  
  # take all nouns, verbs, adjectives
  # look at all the nouns, verbs, and adjectives that modify them 
  subset_df <- subset(annotated_df_lemma, 
                      concept_pos == "NOUN" |
                        concept_pos == "VERB" |
                        concept_pos == "ADJ")
  
  subset_df <- subset(subset_df, 
                      feature_pos == "NOUN" |
                        feature_pos == "VERB" |
                        feature_pos == "ADJ")
  
  # figure out the dependency parsing modifiers that are interesting
  # head is concept, other word is property
  # remember use regular expressions to deal with the pass
  # nsubj, nmod, obj, iobj, amod. obl, 
  # root is the overall head word, which was eliminated earlier 
  
  use_deps <- c("nsubj", "nmod", "obj", "iobj", "amod", "obl")
  
  subset_df <- subset(subset_df, 
                      dependency_relation %in% use_deps)
  
  # tally that up 
  count_df <- plyr::count(subset_df, colnames(subset_df))
  
  # write out that file 
  if(length(file_names) == 1) {
    language_write_out <- language
  } else {
    language_write_out <- gsub("data/", "", file)
    language_write_out <- gsub(".gz", "", language_write_out)
  }
  
  
  write.csv(count_df, 
            file = paste0("concept-feature/", language_write_out, "_concept_features.csv"),
            row.names = F,
            fileEncoding = "UTF-8")
}


