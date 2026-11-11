<script setup lang="ts">
import {onMounted, ref, computed} from 'vue';
import {api} from './services/api';
import type {Meeting} from './types/meeting';
const meetings=ref<Meeting[]>([]), loading=ref(false), error=ref(''), search=ref(''), filter=ref('all'), selected=ref<Meeting|null>(null);
const counts=computed(()=>({total:meetings.value.length, matched:meetings.value.filter(x=>x.reconciliation_status.startsWith('matched')).length, conflicts:meetings.value.filter(x=>x.conflicts.length||x.duplicate_candidate).length, unmatched:meetings.value.filter(x=>['crm_only','calendar_only'].includes(x.reconciliation_status)).length}));
const filtered=computed(()=>meetings.value.filter(m=>(filter.value==='all'||(filter.value==='conflicts'?(m.conflicts.length>0||m.duplicate_candidate):filter.value===m.reconciliation_status)) && JSON.stringify(m).toLowerCase().includes(search.value.toLowerCase())));
async function load(){loading.value=true;error.value='';try{const r=await api.get('/meetings');meetings.value=r.data.items;}catch(e:any){error.value=e?.message||'Unable to load meetings. Is the API running?';}finally{loading.value=false;}}
async function sync(){try{await api.post('/sync');await load();}catch(e:any){error.value=e?.message||'Sync failed';}}
function show(m:Meeting){selected.value=m}
onMounted(load);
</script>
<template>
<main class="shell">
  <header><div><p class="eyebrow">INTERNAL OPERATIONS</p><h1>Event Sync Service</h1><p class="sub">A unified view of CRM and Calendar meetings</p></div><button class="primary" @click="sync">↻ Run sync</button></header>
  <section class="stats">
    <article><span>Total meetings</span><strong>{{counts.total}}</strong></article>
    <article><span>Matched</span><strong>{{counts.matched}}</strong></article>
    <article><span>Conflicts / duplicates</span><strong>{{counts.conflicts}}</strong></article>
    <article><span>Single-source</span><strong>{{counts.unmatched}}</strong></article>
  </section>
  <section class="toolbar"><input v-model="search" placeholder="Search client, title, attendee..." /><select v-model="filter"><option value="all">All meetings</option><option value="conflicts">Conflicts / duplicates</option><option value="calendar_only">Calendar only</option><option value="crm_only">CRM only</option><option value="matched">Matched only</option></select></section>
  <p v-if="error" class="error">{{error}}</p><p v-if="loading" class="muted">Loading meetings…</p>
  <section class="table-wrap" v-else>
    <table><thead><tr><th>Meeting</th><th>Date</th><th>Sources</th><th>Match</th><th>Review</th><th></th></tr></thead>
      <tbody><tr v-for="m in filtered" :key="m.meeting_id" @click="show(m)">
        <td><b>{{m.title.value}}</b><small>{{m.calendar?.location || m.crm?.location || 'Location not provided'}}</small></td>
        <td>{{m.meeting_date||'Unknown'}}</td>
        <td><span v-if="m.calendar" class="tag cal">Calendar</span><span v-if="m.crm" class="tag crm">CRM</span></td>
        <td>{{m.match_confidence?Math.round(m.match_confidence*100)+'%':'—'}}</td>
        <td><span class="status" :class="{warn:m.conflicts.length||m.duplicate_candidate,ok:m.reconciliation_status==='matched'}">{{m.duplicate_candidate?'Duplicate candidate':m.conflicts.length?m.conflicts.length+' conflict(s)':m.reconciliation_status.replaceAll('_',' ')}}</span></td>
        <td><button class="link" @click.stop="show(m)">Details →</button></td>
      </tr><tr v-if="!filtered.length"><td colspan="6" class="empty">No meetings match this filter.</td></tr></tbody>
    </table>
  </section>
  <div v-if="selected" class="overlay" @click.self="selected=null"><aside class="drawer"><button class="close" @click="selected=null">✕</button><p class="eyebrow">MEETING DETAILS</p><h2>{{selected.title.value}}</h2><p class="muted">{{selected.meeting_date}} · {{selected.meeting_id}}</p>
    <div class="detail-block"><h3>Reconciliation</h3><p>Status: <b>{{selected.reconciliation_status}}</b></p><p>Confidence: {{Math.round(selected.match_confidence*100)}}%</p><p v-if="selected.match_reasons.length">Reasons: {{selected.match_reasons.join(', ')}}</p></div>
    <div v-if="selected.conflicts.length" class="detail-block"><h3>Conflicts</h3><div v-for="c in selected.conflicts" :key="c.field" class="conflict"><b>{{c.field}}</b><p>Calendar: {{c.calendar_value}}</p><p>CRM: {{c.crm_value}}</p><small>{{c.note}}</small></div></div>
    <div v-if="selected.duplicate_candidate" class="notice">Possible duplicate within Calendar source. Review before merging.</div>
    <div class="detail-block"><h3>Calendar source · {{selected.sources.calendar_id||'Not present'}}</h3><pre>{{selected.calendar?JSON.stringify(selected.calendar,null,2):'No Calendar record'}}</pre></div>
    <div class="detail-block"><h3>CRM source · {{selected.sources.crm_id||'Not present'}}</h3><pre>{{selected.crm?JSON.stringify(selected.crm,null,2):'No CRM record'}}</pre></div>
  </aside></div>
  <footer>Event Sync Service · Source values are preserved; conflicts are surfaced, not silently overwritten.</footer>
</main>
</template>
