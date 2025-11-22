i want to put more structure around the roadmap object hierarchy

a roadmap should be a comprehensive view of the project, it includes everything that has been completed and everything that is planned;
roadmaps can be broken into tracks, which are made up of sprints, and sprints are broken into tasks;

a task is the smallest unit of work in the framework; it should be small enough that it is a reasonable expectation to complete it within a single token context window for the model being used for vibe coding in the project; non-documentation quality gates are typically not be a requirement to mark a task complete; the primary function of a task is to create a managable unit of work for the vibe coding model; completion of a task should typically result in a documentation update, git commit, and push;

a sprint is a group of tasks that are highly related to one another such that it makes sense to group them to be built together; the tasks within a given sprint likely have many dependencies between one another; there's no limit to the number of tasks that could be included in a sprint; completion of a sprint typcially requires passing of all quality gates, and should also include a doc update, git commit and push;

sprint planning should always attempt to match specialized agents to sprint tasks and identify opportunities for parallelism across tasks;

the sprint retroactive stage should include an analysis of tasks across all completed and future sprints without an assigned specialized agent and attempt to group similar tasks to find opportunities to create new agents; when new agents are created through this process, they should be assigned to the incomplete sprint tasks where they are relevant;

within the roadmap, sprints can be grouped in to tracks; tracks are a group of sprints that have dependencies between one another, but do not have major dependencies to sprints in other tracks; said another way, sprint tracks have the opportunity to be developed in parallel without being blocked by the other tracks;

status options for tasks, sprints, and tracks
- not started
- in progress
- complete
- production ready
- deployed
- won't do

in addition to these statuses, an object always is either "blocked" or "not blocked"; an object that is "blocked" will have incomplete blockers; in other words, it has dependencies to move forward that have not been completed;

a depedency is defined as a task/sprint/track relying on another's completion to move into a specific status; for example task 1 might have a dependency on the completion of task 2 to move to "production ready" but task 1 could still be developed until it was in the "complete" stage. If task 1 got to "complete"

all objects should have a list of the other obejcts that are blockers for it's completion and the stage each blocker is gating;

everything here is a suggestion and is open for discussion; develop a comprehesive point of view about the roadmap object hierarchy; consider
- what objects may be required for the project
- relationships between the objects
- statuses for the objects
- developer workflow when leveraging the framework
- methods to track and manage the roadmap state with versioning
- develop a naming convention for versioning of projects that ties to the roadmap object hierarchy
- include any trade offs of design decisions in your recommendations

write your findings to a report in the docs