# workable-to-csv

the point is to get any kind of candidate details from workable into a spreadsheet without
[contacting their support](https://help.workable.com/hc/en-us/articles/115014887828-How-do-I-export-candidate-data)
to initiate a full export. make sure you actually need this: you might be able
to get what you want with their built-in exports.

apis used:
* https://workable.readme.io/reference/jobs
* https://workable.readme.io/reference/job-candidates-index
* https://workable.readme.io/reference/job-candidates-show

you will need:
* an api token from https://www.workable.com/backend/account/integrations
* an understanding of python dictionary comprehensions; see `DESIRED_CANDIDATE_ATTRIBUTES`
* patience (the workable api is severely rate limited)


good luck…
