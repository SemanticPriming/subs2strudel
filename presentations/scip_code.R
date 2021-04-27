library(rio)
setwd(here::here())

# This is a big file!
english <- import("en_concept_features.csv.zip")

# How big
nrow(english)

# load other norms
erin <- import(file.choose())

# words
words <- c("house", "conference", "night", "dry")

# subsets
english <- subset(english,
                  feature_lemma %in% words | concept_lemma %in% words)


erin <- subset(erin,
               cue %in% words & where == "b")
erin$id <- paste(erin$cue,
                 erin$translated)

english_forward <- subset(english,
                          feature_lemma %in% words)
english_forward$id <- paste(english_forward$feature_lemma, 
                           english_forward$concept_lemma)

english_backward <- subset(english, concept_lemma %in% words)
english_backward$id <- paste(english_backward$concept_lemma, 
                             english_backward$feature_lemma)

english_forward_merge <- merge(english_forward[ , c("id", "freq", "feature_lemma") ],
                               unique(erin[ , c("id", "normalized_translated") ]), 
                               by = "id", all = T)


english_backward_merge <- merge(english_backward[ , c("id", "freq", "concept_lemma") ],
                               unique(erin[ , c("id", "normalized_translated") ]), 
                               by = "id", all = T)


#get normalized frequency
english_forward_totals <- tapply(english_forward$freq, 
                                 english_forward$feature_lemma,
                                 sum)

english_backward_totals <- tapply(english_backward$freq, 
                                  english_backward$concept_lemma,
                                 sum)

english_forward_merge$freq_normal <- NA
english_backward_merge$freq_normal <- NA
english_forward_merge$freq[is.na(english_forward_merge$freq)] <- 0
english_backward_merge$freq[is.na(english_backward_merge$freq)] <- 0
english_forward_merge$feature_lemma[english_forward_merge$id == "dry lack"] <- "dry"

english_backward_merge$concept_lemma[english_backward_merge$id == "dry moist"] <- "dry"
english_backward_merge$concept_lemma[english_backward_merge$id == "conference talk"] <- "conference"

for (word in words){
  english_forward_merge$freq_normal[english_forward_merge$feature_lemma == word] <- 
    english_forward_merge$freq[english_forward_merge$feature_lemma == word] / 
    english_forward_totals[word] * 100
  
  english_backward_merge$freq_normal[english_backward_merge$concept_lemma == word] <- 
    english_backward_merge$freq[english_backward_merge$concept_lemma == word] / 
    english_backward_totals[word] * 100
}

english_forward_merge$normalized_translated[is.na(english_forward_merge$normalized_translated)] <- 0
english_backward_merge$normalized_translated[is.na(english_backward_merge$normalized_translated)] <- 0

cutoffs <- seq(0, 3, .1)

library(lsa)

answers <- data.frame(word = character(),
                      cutoff = numeric(),
                      cosine = numeric(),
                      forward = character())

for (cut in cutoffs){
  
  for (word in words){
    
    temp <- subset(english_forward_merge,
                   feature_lemma == word &
                     freq_normal >= cut)
    
    temp2 <- subset(english_backward_merge,
                   concept_lemma == word &
                     freq_normal >= cut)
    
    answers <- rbind(answers, 
                     c(
                       word, cut,
                       cosine(temp$normalized_translated, temp$freq_normal),
                       "backward" # I labeled this backwards
                       #forward dataset is feature to concept
                       #feature to concept is dependent to head
                     ))
    answers <- rbind(answers,
                     c(
                       word, cut,
                       cosine(temp2$normalized_translated, temp2$freq_normal),
                       "forward" # labeled this backwards
                       #backward dataset is concept to feature
                       #concept to feature is head to dependent 
                     ))
  }
  
}

colnames(answers) <- c("word", "cutoff", "cosine", "forward")

answers$cosine <- as.numeric(answers$cosine)
answers <- subset(answers,
                  cosine > 0)

write.csv(answers, "example_answers.csv", row.names = F)
