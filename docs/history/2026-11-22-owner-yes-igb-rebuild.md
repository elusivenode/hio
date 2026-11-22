<!-- The owner's message to Claude Code, 2026-11-22, verbatim. Recorded by OD-0230. It answered Claude's question: "Decision: do you authorise a rebuilt IGB series without the 1 October 2020 stub record? A yes authorises: a proposed spec version that names the one excluded record and why; a small worker change so the build tool can honour an exclusion listed in a spec, with tests on invented data; a local build with my real-data check. It accepts nothing and touches no other fund. Nothing downstream uses IGB today, so leaving it flagged and uncorrected is also reasonable." -->

**Owner's message**

Yes. What we want to do here is build up our data series for factor and portfolio construction with any small corrections we need. What concerns me here is we have no database to persist our series.
I favour a medallion architecture and modern elt processes to store bronze, silver and gold data. 
Critique this idea
