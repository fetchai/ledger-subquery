import { OnApplicationShutdown } from '@nestjs/common';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { SubqlCosmosMessageFilter, SubqlCosmosEventFilter } from '@subql/common-cosmos';
import { DictionaryQueryEntry } from '@subql/types-cosmos';
import { NodeConfig } from '../configure/NodeConfig';
import { SubqueryProject } from '../configure/SubqueryProject';
import { ApiService, CosmosClient } from './api.service';
import { DictionaryService } from './dictionary.service';
import { DsProcessorService } from './ds-processor.service';
import { DynamicDsService } from './dynamic-ds.service';
import { BlockContent } from './types';
export declare function eventFilterToQueryEntry(filter: SubqlCosmosEventFilter): DictionaryQueryEntry;
export declare function messageFilterToQueryEntry(filter: SubqlCosmosMessageFilter): DictionaryQueryEntry;
export declare class FetchService implements OnApplicationShutdown {
    private apiService;
    private nodeConfig;
    private project;
    private dictionaryService;
    private dsProcessorService;
    private dynamicDsService;
    private eventEmitter;
    private latestBestHeight;
    private latestFinalizedHeight;
    private latestProcessedHeight;
    private latestBufferedHeight;
    private blockBuffer;
    private blockNumberBuffer;
    private isShutdown;
    private useDictionary;
    private dictionaryQueryEntries?;
    private batchSizeScale;
    private templateDynamicDatasouces;
    constructor(apiService: ApiService, nodeConfig: NodeConfig, project: SubqueryProject, dictionaryService: DictionaryService, dsProcessorService: DsProcessorService, dynamicDsService: DynamicDsService, eventEmitter: EventEmitter2);
    onApplicationShutdown(): void;
    get api(): CosmosClient;
    syncDynamicDatascourcesFromMeta(): Promise<void>;
    getDictionaryQueryEntries(): DictionaryQueryEntry[];
    register(next: (value: BlockContent) => Promise<void>): () => void;
    updateDictionary(): void;
    init(): Promise<void>;
    checkBatchScale(): void;
    getLatestBlockHead(): Promise<void>;
    latestProcessed(height: number): void;
    startLoop(initBlockHeight: number): Promise<void>;
    fillNextBlockBuffer(initBlockHeight: number): Promise<void>;
    fillBlockBuffer(): Promise<void>;
    private nextEndBlockHeight;
    resetForNewDs(blockHeight: number): Promise<void>;
    private dictionaryValidation;
    private setLatestBufferedHeight;
    private getBaseHandlerKind;
    private getBaseHandlerFilters;
}
