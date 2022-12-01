import datetime as dt
import sys
import time
import unittest
from pathlib import Path

repo_root_path = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(repo_root_path))

from tests.helpers.entity_test import EntityTest
from src.genesis.helpers.field_enums import ReleaseVersionFields
from tests.helpers.graphql import test_filtered_query


class TestReleaseVersion(EntityTest):
    git_tag = "v0.3.0"
    git_hash = "3ac0d0143547f9a0cc3462a916933e10ea5e747d"
    id = "0"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_release_version(self):
        release_versions = self.db_cursor.execute(ReleaseVersionFields.select_query()).fetchone()
        self.assertIsNotNone(release_versions, "\nDBError: table is empty - maybe indexer did not find an entry?")
        self.assertEqual(release_versions[ReleaseVersionFields.id.value], self.id, "\nDBError: id does not match")
        self.assertEqual(release_versions[ReleaseVersionFields.git_tag.value], self.git_tag, "\nDBError: git tag does not match")
        self.assertEqual(release_versions[ReleaseVersionFields.git_hash.value], self.git_hash, "\nDBError: git hash does not match")

    def test_retrieve_version(self):

        release_version_nodes = """
            {
                id,
                gitHash,
                gitTag
            }
            """

        def filtered_release_version_query(_filter):
            return test_filtered_query("releaseVersions", _filter, release_version_nodes)

        # query release version, filter by id
        filter_by_to_id_equals = filtered_release_version_query({
            "id": {
                "equalTo": self.id
            }
        })

        # query release version, filter by git tag
        filter_by_git_tag_equals = filtered_release_version_query({
            "gitTag": {
                "equalTo": self.git_tag
            }
        })

        # query release version, filter by git hash
        filter_by_git_hash_equals = filtered_release_version_query({
            "gitHash": {
                "equalTo": self.git_hash
            }
        })

        for (name, query) in [
            ("by gitTag equals", filter_by_git_tag_equals),
            ("by gitHash equals", filter_by_git_hash_equals),
            ("by id equals", filter_by_to_id_equals)
        ]:
            with self.subTest(name):
                result = self.gql_client.execute(query)
                """
                ["releaseVersions"]["nodes"][0] denotes the sequence of keys to access the message contents queried for above.
                This provides {"releaseVersions":id, "releaseVersions":gitTag, "releaseVersions":gitHash
                which can be destructured for the values of interest.
                """
                release_versions = result["releaseVersions"]["nodes"]
                self.assertNotEqual(release_versions, [], "\nGQLError: No results returned from query")
                self.assertEqual(release_versions[0]["id"], self.id)
                self.assertEqual(release_versions[0]["gitTag"], self.git_tag)
                self.assertRegex(release_versions[0]["gitHash"], self.git_hash)


if __name__ == '__main__':
    unittest.main()
