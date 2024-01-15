This is just a TODO list for now! More information incoming.

1. Add the basic Robert Plutchik's emotions as a way for the user to describe their reaction to each toot
    - see also http://atlasofemotions.org/#states/sadness on examples of emotions going from least intense to most intense
1. There should also be an "indifferent" option. Maybe boredom? Need to better understand how plutchiks framework is designed.
1. This information can be used by the user to understand how he is reacting to his feeds.
1. This can be used to query, for example, at what time he is feeling what emotions and what is his overall reaction to specific users.
1. Since Plutchik emotions can be combined, we can combine reaction to individual toots by their proximity on the timeline and try to guess what emotion the user psique is going towards on each session.
1. Use that to train a BERT/BERTIMBAU emotion classifier :-) like a personal algorithm (study finetuning BERT vs finetuning goemotions):
    - https://medium.com/neuronio-br/da-an%C3%A1lise-de-sentimentos-para-o-reconhecimento-de-emo%C3%A7%C3%B5es-uma-hist%C3%B3ria-pln-171f27734c56
    - https://blog.research.google/2021/10/goemotions-dataset-for-fine-grained.html
1. Need to better understand whether there would be one model for each language, or one can be used for everything.
1. As the user model grows stronger, it can be used to filter incoming content.


References:

- [LeIA](https://github.com/wpcasarin/LeIA)
