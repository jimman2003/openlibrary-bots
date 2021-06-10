#!/usr/bin/env python3

import copy
import gzip

from olclient.bots import AbstractBotJob


class TrimTitleJob(AbstractBotJob):
    @staticmethod
    def needs_trim(
        work_title: str,
    ) -> bool:  
        # it's good practice to make a check method for the pattern you're looking for
        """Returns True if Edition title needs to have whitespace removed. Return false otherwise"""
        return work_title.strip() != work_title

    def run(self) -> None:  # overwrite the AbstractBotJob run method
        """Strip leading and trailing whitespace from edition titles"""
        self.dry_run_declaration()

        comment = "trim whitespace"
        with gzip.open(self.args.file, "rb") as fin:
            for row in fin:
                # extract info from the dump file and check it
                row, json_data = self.process_row(row)
                if json_data["type"]["key"] != "/type/work":
                    continue  # this handles full dump (instead for work dump)
                if not self.needs_trim(json_data["title"]):
                    continue

                # the database may have changed since the dump was created, so call the
                # OpenLibrary API and check again
                olid = json_data["key"].split("/")[-1]
                work = self.ol.Work.get(olid)
                if work.type["key"] != "/type/work":
                    continue  # skip deleted editions
                if not self.needs_trim(work.title):
                    continue

                # this edition needs editing, so fix it
                old_title = copy.deepcopy(work.title)
                work.title = work.title.strip()
                self.logger.info(
                    "|".join([olid, old_title, work.title])
                )  # don't forget to log modifications!
                self.save(lambda: work.save(comment=comment))


if __name__ == "__main__":
    job = TrimTitleJob()

    try:
        job.run()
    except Exception as e:
        job.logger.exception("")
        raise e
