#!/usr/bin/env python3
"""
Query Performance Monitor - Track and optimize SQL query performance.

This module provides utilities to monitor query execution times, identify
slow queries, and suggest optimizations.
"""

import time
import logging
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceMetrics:
    """Performance metrics for a single query execution"""
    query_id: str
    natural_language_query: str
    sql_query: str
    execution_time: float
    result_count: int
    success: bool
    error_message: Optional[str]
    timestamp: datetime
    complexity_score: float
    optimization_applied: bool
    metadata: Dict[str, Any]


class QueryPerformanceMonitor:
    """Monitor and track SQL query performance"""
    
    def __init__(self, metrics_file: str = "back-end/cache/performance_metrics.json"):
        self.metrics_file = metrics_file
        self.metrics: List[QueryPerformanceMetrics] = []
        self.performance_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'average_execution_time': 0.0,
            'slow_queries_count': 0,
            'optimization_success_rate': 0.0
        }
        
        # Load existing metrics
        self._load_metrics()
        
        # Performance thresholds
        self.slow_query_threshold = 10.0  # seconds
        self.very_slow_query_threshold = 30.0  # seconds
        
    def _load_metrics(self):
        """Load performance metrics from disk"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    
                for item in data.get('metrics', []):
                    # Convert timestamp string back to datetime
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                    self.metrics.append(QueryPerformanceMetrics(**item))
                    
                self.performance_stats = data.get('stats', self.performance_stats)
                logger.info(f"Loaded {len(self.metrics)} performance metrics")
                
            except Exception as e:
                logger.error(f"Failed to load performance metrics: {e}")
    
    def _save_metrics(self):
        """Save performance metrics to disk"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
            
            # Convert metrics to serializable format
            serializable_metrics = []
            for metric in self.metrics:
                metric_dict = asdict(metric)
                metric_dict['timestamp'] = metric.timestamp.isoformat()
                serializable_metrics.append(metric_dict)
            
            data = {
                'metrics': serializable_metrics,
                'stats': self.performance_stats,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save performance metrics: {e}")
    
    def record_query_performance(self,
                                query_id: str,
                                natural_language_query: str,
                                sql_query: str,
                                execution_time: float,
                                result_count: int = 0,
                                success: bool = True,
                                error_message: Optional[str] = None,
                                complexity_score: float = 0.0,
                                optimization_applied: bool = False,
                                metadata: Optional[Dict[str, Any]] = None) -> QueryPerformanceMetrics:
        """Record performance metrics for a query execution"""
        
        metric = QueryPerformanceMetrics(
            query_id=query_id,
            natural_language_query=natural_language_query,
            sql_query=sql_query,
            execution_time=execution_time,
            result_count=result_count,
            success=success,
            error_message=error_me")ns'])}['suggestiooppjoin(ons: {', '.stit(f"  Suggein
        priority']}")tion_prp['optimizaty: {op"  Priorint(f      pri)
  .."][:50]}.p['pattern' {op"  Pattern:nt(f  pri:
      esportunitiin op   for opp )}")
 rtunitiesn(oppo{leties: ortuniOppzation f"\nOptimi    print(
ities()ion_opportunzat_optimior.identifys = monitnitie   opportu
     ue}")
 {val {key}:rint(f" :
        pitems()in summary., value for key  y:")
  ummarerformance S print("P()
   ummaryerformance_sr.get_p= monito summary rt
   erate repoGen    
    # 
    )
ess=Truecc       su
 ult_count=1,es     r=15.2,
   timen_ executio",
       ..omers ON . custrs JOINM orde*) FROOUNT(CT Cry="SELEque       sql_uery",
 on qti aggregamplexe_query="Co_languag    natural_2", 
    id="testery_      qu  formance(
uery_peror.record_qmonit   
    )
 
    ueess=Tr   succ    nt=100,
 result_cou        me=2.5,
tion_ti      execu  mers",
 FROM custo00 * 1"SELECT TOP=  sql_query     mers",
 stoll cu me aery="Showguage_qutural_lan     nast_1",
   ry_id="te        quence(
ery_performa_qurecord  monitor.
   metricseryqusome # Simulate    
     r()
eMonitoncerformayP = Quertor monisting
   e and tee usagExampl  # ain__":
   == "__m_name__


if _pperrn wra   retu    
    raise
)
                     _}
ame_': func.__n{'functionetadata=         m    ),
   ssage=str(eme     error_          ss=False,
  succe          ,
     on_timeutiime=execion_txecut       e   te',
      rageneo ed t'Failry=l_quesq           
      'Unknown', else0]) if argsrgs[uery=str(alanguage_ql_ natura               id,
ry_id=query_        que     mance(
   ery_perforcord_qumonitor.rerformance_         pe_time
   start) - time.time(tion_time = cu       exe  s e:
   Exception a except            
   t
     return resul                   
       )
  
        c.__name__}n': fun{'functiometadata=              s,
  =succesuccess   s             
ion_time,e=executim_ton executi          
     [:500],ql_query)tr(sry=s sql_que         0],
      uery)[:20l_qaturay=str(nquerlanguage_  natural_           
   d,y_iry_id=querque           ance(
     performry_record_queitor.mance_mon    perfor
                  e True
  ls) eess'succult, 'reshasattr(, True) if uccess'esult, 'setattr(r= g   success         
 Unknown' ') elsequery't, 'sql_esulhasattr(r if , 'Unknown')l_query'result, 'sqtattr(y = geuerl_qsq           own')
 e 'Unknelsgs rgs[0] if arery', aanguage_quural_let('natkwargs.gal_query = urnat      
      lablef avaim result iinfo fro query  Extract  #   
                   
_time- startime() me.t = tition_time execu           gs)
**kwarc(*args, = fun result         try:
                
 "
  )}_timetartnt(s{iry__id = f"que     query)
   ime(.ttime_time =        startargs):
 gs, **kwpper(*ar
    def wra"ormance""query perfor tor to monit"Decora
    ""mance(func):uery_perfortor_q
def monior()

ceMonitformaneryPer= Quitor _monformancetance
perinstor ormance monierf Global p

#ort
urn repet
        r}")utput_fileted to {oporport exance re(f"Performinfoogger. l   
            )
nt=2ort, f, indeson.dump(rep   j        as f:
  _file, 'w')utput with open(o              
 mestamp"]
["tielse query, datetime) mestamp"]ti["ce(querynstanisiformat() if .isomp"]staery["timequ] = ""timestamp    query[             
   ry:mp" in queif "timesta               list:
 query_ry in      for que
       ies"]]:quer"failed_ report[s"],w_querieloort["st in [repquery_lis      for   lization
ON seriafor JS to strings bjectsdatetime o  # Convert            
    }
       ce_stats
anlf.perform_stats": serformance"pe            unities(),
orttion_opptimizaify_opent self.idies":nitportuation_opmizopti"         ],
   eries()led_quget_faiself. q in q) forct(sdiueries": [a"failed_q           )],
 queries(_slow_elf.getq in sfor sdict(q) s": [aielow_quer     "s    mary(),
   rmance_sumperfot_elf.gemary": sum   "s         ,
.isoformat()ow()time.n: dateed_at""generat            {
 report =    """
    ce reporterformanrehensive pomp""Export c      "json"):
  nce_report.marfor: str = "pet_filepuf, out(selce_reportrformant_pepor
    def exrics()
    ve_met_sa       self.
     metrics")ormance } old perfd_countmoveup {ref"Cleaned gger.info(      lo
      > 0:oved_count    if rem   )
  icslf.metr len(seount -al_c origint =ed_coun       remov  
 te]
      f_datamp > cutof.timescs if metri in self.mm for mics = [f.metr       sel     
 
   etrics)n(self.mount = leinal_corig     o_keep)
   days_ta(days=medelt - tie.now()imetf_date = dattof       cuys"""
 ied da specifhaner tetrics oldemove m"""R
        nt = 30):keep: ilf, days_to_trics(senup_old_me  def clea   
  ggestions
 urn su        ret

        )ion"aginat p considerrge -y laet is versult snd("Repegestions.ap         sug:
   nt > 10000ult_coues metric.r      if       
  exes")
 er indprop and ensure tionsndiOIN co Jd("Optimizeentions.appes        suggshold:
    _query_thre self.slowtime >xecution_metric.eand  sql_upper N" in "JOI
        if         tables")
riedes on que indexd("Reviewns.appen   suggestio        ")
 queriesmaller ing into sder break("Consitions.appendes       sugg  d:
   thresholquery_ow_ry_slelf.ve > secution_timeetric.ex  if m    
      
    t set")resule to limit aus clAdd TOPd("appenns.suggestio        
     sql_upper:ot inP" nif "TO          
     ")
 ultsfilter rese to HERE claus("Add Wons.appenduggesti      sr:
      sql_uppein HERE" not  if "W
            r()
   l_query.uppe= metric.sqper _up        sql
ns = []   suggestio"
      query""for a slows estion suggptimization oGenerate"""        
List[str]:cs) -> trianceMermyPerfotric: Querons(self, meuggestition_ste_optimizaneradef _ge     
  g
 or groupincate f00]  # Trunern[:1attreturn p  
              strip()}"
 {from_part.OMtrip()} FRelect_part.s f"{s     return     se ""
   pattern el" in"WHEREern and " in patt0] if "FROM"WHERE")[].split([1")"FROMlit(sprn.pattefrom_part =             pattern
se  pattern elFROM" in")[0] if "lit("FROMern.sp= pattct_part    sele        pattern:
 n " iLECT   if "SE     ure
ct struct main # Extra
               clauses
 # TOPattern)   N", p, "TOP+\d+"ub(r"TOP\sre.s  pattern =     
  umbers N #n) ", patterBER\b", "NUM(r"\b\d+ern = re.sub     pattls
   raiteing l # Str, pattern) "'VALUE'"']*'", sub(r"'[^attern = re.s
        pderth placeholvalues wic ace specifi      # Repl     
  er()
   ql_query.upppattern = s            
   import re
      tifiers
   idenues and pecific val son - removeractitern ext pat   # Simple
     s""" querie similarpingrour g query fom SQL pattern fro"Extract a      ""r:
  > sty: str) -ersql_quern(self, _query_pattxtract    def _e 
   rse=True)
"], revetime_spent["total_a x: x, key=lambdrtunities sorted(oppo   return  
      })
                 [0])
    ns(queriesiosuggestptimization_erate_o: self._genggestions" "su                  ry,
 age_quelangual_uries[0].nat queruery":mple_q  "exa         
         "medium",old else eshow_query_thrself.very_slime > f avg_th" ity": "higation_prioriptimiz  "o                 ),
 eries]for q in qucution_time ([q.exeent": sumspe_total_tim        "             avg_time,
e":cution_timverage_exe"a              
      queries),t": len("query_coun                 rn,
   ttetern": pa"pat              
      pend({aportunities.   opp     
        ueries])or q in qtion_time f[q.execun(s.meatatistice = sg_tim         av
       times multiple rn appears Patte:  #eries) >= 2qulen(       if   
   ms():terns.iteatn query_p, queries ir pattern fo         
    )
  icpend(metrattern].appatterns[puery_ q              uery)
 etric.sql_qpattern(mry_ct_queextraf._attern = sel  p          d
    enhanced be ulng - coern matchile patt  # Simp           
   threshold:slow_query_ > self.on_time.executi metricandc.success    if metri
         :.metricsic in selfmetr  for t)
      dict(lis= default_patterns   query   erns
   milar patts by siGroup querie  #   
      
      = []s itieopportun     ""
   "timization from opould benefitat cqueries thntify """Ide
        ]:tr, Any][sict-> List[D) (selftunitiesoration_oppify_optimizdef ident    mary
    
sumeturn  r   
       
     lse 0> 0 eer_avg 100) if old_avg *  / older- older_avg)t_avg recenabs(( = tage"]end_percenary["trmmsu      
          degrading" "sevg el older_ant_avg < receoving" if"imprtrend"] = ce_man"perforary[umm      s          0])
lder_1 in o for mon_timetiexecum.an([.mestatistics_avg =  older            ])
    recent_10for m incution_time .mean([m.exetisticsavg = staent_    rec    :
        der_10      if ol 
                 se []
 20 eltrics) >=essful_mesucc10] if len(20:-stamp)[- x: x.timekey=lambdaics, cessful_metrted(sucsor= older_10        0:]
     p)[-1x.timestam=lambda x: rics, keyul_metssfcceorted(su0 = s  recent_1          >= 10:
 ful_metrics)len(success        if 
trendsance rm# Perfo    
           }
   one
       Nmetrics elself.at() if ses]).isoformself.metricfor m in m.timestamp : max([e"timst_query_     "la       ]),
ion_appliedmizats if m.optielf.metricin sen([m for m d_count": l_applieimization"opt        
    t_metrics),: len(recenries"4h_querecent_2          "hold]),
  _query_thresery_slow self.vtion_time >ecuf m.excs iul_metrisfsuccesin or m : len([m fries_count"y_slow_que   "ver
         ),hold]ry_thresque> self.slow_ution_time ecics if m.exl_metrsfu in succes([m for m": lenueries_count"slow_q     
        else 0,sful_metricsces]) if sucicscessful_metrfor m in sucn_time xecutioan([m.eics.meditatist": sion_timeutian_exec      "med       0,
metrics elsecessful_ucrics]) if sessful_met m in succorme fecution_ti.ex.mean([mcs statistie":cution_time_exe  "averag     0,
      rics else self.metics) iflf.metr/ len(seetrics) ul_mcessf": len(sucrates_    "succes  
      cs),ssful_metri len(succeics) -en(self.metrqueries": l"failed_    
        l_metrics),ccessfu": len(suriesl_quessfusucce    "        metrics),
lf. len(seies":al_quertot "          ary = {
       summ   
  ess]
     f m.succrics i self.met[m for m inics = _metrcessful        suc
=24)]ta(hours timedel.now() -p > datetimemestam if m.ticsetriself.mr m in rics = [m forecent_met  
        "}
      a availableance dat"No performage": urn {"mess    ret       ics:
 trself.me     if not ""
   e summary"ncormaensive perfmpreh"""Get co      ]:
  Anyct[str,  -> Diummary(self)ance_s_perform get
    def ]
   ue)[:limitrse=Trrevestamp, a x: x.timembdy=la keeries,ed_quilrn sorted(faetu       ress]
 f not m.succetrics ielf.m in s [m for med_queries =       fail""
 ies" failed quert recent"Ge  ""  
    ics]:anceMetrrmryPerfo> List[Quent = 10) -imit: ilf, les(seueriiled_qdef get_fa    
    it]
e)[:limeverse=Tru, rn_timetioa x: x.execukey=lambdul_queries, successfn sorted(tur    ress]
    cce.suetrics if m self.mm inr  = [m foriescessful_que      sucs"""
  ueriet qweslo"Get the s    ""ics]:
    trmanceMeyPerforuer List[Q10) ->mit: int = elf, li_queries(sdef get_slow
    
    zed_queries)timi) / len(opimizationsccessful_opt] = len(suate'success_rptimization_ts['oormance_staelf.perf       s   old]
  ry_thresh_queself.slowme < on_tiecutid m.ex.success anes if mmized_queri in optior m = [m fptimizationsl_osuccessfu          
  ries:ized_queptim if o    ied]
   ion_appl m.optimizat if.metricsm in self [m for queries =optimized_
        ess rateization succte optim# Calcula              
 = 1
 t'] +_counqueriesats['slow_rmance_sterfo.p self        
   old:ery_threshquf.slow_> sele n_timutiometric.execf 
        iw queriesunt sloCo#               
_avg
  newme'] = ion_tige_executrats['aveormance_staperfelf.         scessful
   total_sucion_time) / c.execut) + metriessful - 1)ccsug * (total_urrent_avew_avg = ((c     n   ]
    ution_time'exec['average_atsformance_stlf.per = seurrent_avg       c
     > 0:ssful al_succeot if t']
       _queries['successful_stats.performanceul = selfssftal_succe      to  ion time
erage execut # Update av   
       
      1es'] +=iled_querice_stats['faerformanelf.p         s
          else: += 1
 s']iel_querfusuccesstats['nce_slf.performa  se    
      c.success:    if metri      
   1
   es'] += 'total_querie_stats[rmancfoelf.per      s"""
  ticsmance statisrfor pe aggregatedate"Up        ""trics):
rmanceMeryPerforic: Queelf, metance_stats(srmate_perfo def _upd  
   
  turn metric     re
          ics()
 save_metr self._
            0:s) % 10 ==self.metric     if len(y
   allcs periodicmetrito-save    # Au        
   ")
  natioizimer optidf}s - Constime:.2ecution_ {ex slow query:ry"Ver.error(f       loggeold:
     threshw_query_elf.very_slo> se ion_timf execut       i       
 
     ):100]}..."uage_query[ral_langtu2f}s - {naion_time:.utec{exed: ctery detelow qung(f"Slogger.warni       hold:
     hres_query_t self.slowion_time > execut  ifies
      ow quer    # Log sl
    
        )icetrs(mtatformance_se_perdat_up    self.
    d(metric)en.app.metrics    self  
           )
      {}
  tadata ormetadata=me           lied,
 mization_appied=optiion_applmizat        opti   ore,
 mplexity_sccoity_score=omplex        cw(),
    atetime.notimestamp=d    
        ssage,