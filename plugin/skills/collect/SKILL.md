---
name: collect
description: Load before writing a plan step that collects from Reddit, what people posted in a subreddit or about a subject.
group: planning
collects-with: reddit
evidence: web
collect-tools:
  - search_reddit
  - browse_subreddit
  - get_post
keep-from:
  - get_post
identifier: '^https://www\.reddit\.com/r/[A-Za-z0-9_]+/comments/[a-z0-9]+/'
---

# Collecting from Reddit

This skill has two halves. Read the half for the job you have: "Planning a step"
when you are writing a plan, "Collecting" when you are running a step.

## Planning a step

Reddit is the right tool when the answer is what people posted: first-hand
reports, complaints, rumours, how a community reacted, who said what and when.
It is the wrong tool for official statements, news articles or documents; plan
those with a web tool.

Write the action as a search phrase, then optionally a subreddit and a time
span, separated by commas. Three example actions:

    product X recall, r/productx, 2025-03
    Acme warehouse fire
    layoffs at Acme, r/cscareerquestions

One subject per step. Two subjects are two steps.

## Collecting

You have three Reddit tools, `search_reddit`, `browse_subreddit` and `get_post`,
and two of rk's, `keep` and `fetch`. Work through these steps in order.

1. **Plan your searches.** Turn the action into three to six searches:
   - the subject in the action's own words;
   - other phrasings people would use: a product's nickname, a misspelling, the
     company instead of the product;
   - the same searches restricted to the subreddit the action names, and to
     other subreddits where the subject is discussed.
   `time_filter` counts back from today (`day`, `week`, `month`, `year`, `all`).
   For a time span in the past, pick the shortest filter that still reaches it,
   and judge each post by its `published` date.
2. **Run the searches** with `search_reddit`. When the action names a
   subreddit, also call `browse_subreddit` on it with `sort` set to `new`:
   Reddit's search index lags, and the newest posts are only found by browsing.
   Search again when a result points somewhere better, such as a subreddit you
   had not thought of.
3. **Pick the threads to read.** Read each result's title and text against the
   action. Choose the threads that look like they answer the action.
4. **Read each chosen thread in full** with `get_post`, passing the thread's
   `link` from the listing as `url`. Judge again, now with the comments in front
   of you, whether the thread answers the action.
5. **Keep each thread that answers the action** with `keep`. One item per
   thread:
   - `call`: the number of the `get_post` call that read the thread, from its
     `<call n="…">` tag;
   - `identifier`: the thread's own address, the `link` of the `post` in that
     `get_post` answer, copied exactly. It starts
     `https://www.reddit.com/r/<subreddit>/comments/<thread id>/`;
   - `title`: the post's title, on one line.
   You can call `keep` more than once. Keep from `get_post` answers only: a
   search listing is how you find threads, and the thread itself is what you
   keep.
6. **Fetch a linked article** with `fetch` when the action is about what that
   article says, for example a news report a post links to. Pass the address
   exactly as it is written out in the post or comment.
7. **Finish** when you have kept every thread that answers the action, or when
   a tool says the budget is spent.

Keep the post's link. Never keep a comment's link. A comment's link starts
with the same thread address, but it names one comment, not the thread. Copy the `link` of the `post`, not of a comment, even though both start with the thread address.
