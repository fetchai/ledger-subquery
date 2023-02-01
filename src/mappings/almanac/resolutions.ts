import {AlmanacRecord, AlmanacResolution, Contract, Interface,} from "../../types";

export async function cacheAlmanacResolution(contractId: string, agentId: string, record: AlmanacRecord): Promise<void> {
  try {
    logger.info(`[cacheAlmanacResolution] (recordId: ${record.id}): caching record`);
    const resolutionEntity = AlmanacResolution.create({
      id: record.id,
      agentId,
      contractId,
      recordId: record.id,
    });
    await resolutionEntity.save();
  } catch (error) {
    logger.error(`[cacheAlmanacResolution] (recordId: ${record.id}): ${error.stack}`);
  }
}

export async function expireAlmanacResolutionsRelativeToHeight(height: bigint): Promise<void> {
  // NB: resolution, record, and registration ID are the same across related entities.
  const expiringResolutionIdsSql = `SELECT res.id
                              FROM app.almanac_resolutions res
                              JOIN app.almanac_registrations reg
                                ON res.id = reg.id
                              WHERE reg.expiry_height <= ${height}
  `;
  const expiringResolutionIds = await store.selectRaw(expiringResolutionIdsSql);

  // NB: will throw an error if any promise rejects.
  await Promise.all(expiringResolutionIds.map(r => expireAlmanacResolution(String(r.id))));
}

export async function expireAlmanacResolution(id: string): Promise<void> {
  try {
    logger.info(`[expireAlmanacResolution] (recordId: ${id}): expiring record`);
    await AlmanacResolution.remove(id);
  } catch (error) {
    logger.warn(`[expireAlmanacResolution] (recordId: ${id}): ${error.stack}`);
  }
}

